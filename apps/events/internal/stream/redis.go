// Package stream wraps go-redis as a thin `pipeline.StreamReader` adapter.
//
// Responsibilities:
// - Ensure the consumer group exists (idempotent) on startup.
// - Optionally XAUTOCLAIM messages left pending by a crashed consumer.
// - Return messages with the `payload` field decoded as bytes, hiding the
//   underlying flat-map Stream entry shape from the pipeline.
package stream

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"

	"github.com/ozzy1986/ozzb2b/apps/events/internal/pipeline"
)

type Reader struct {
	rdb        *redis.Client
	stream     string
	group      string
	consumer   string
	claimIdle  time.Duration
	lastClaim  time.Time
	claimEvery time.Duration
	logger     *slog.Logger
}

type Config struct {
	RedisURL   string
	Stream     string
	Group      string
	Consumer   string
	ClaimIdle  time.Duration
	ClaimEvery time.Duration
	Logger     *slog.Logger
}

// Connect opens a Redis connection, ensures the group exists and returns a
// ready-to-use Reader.
func Connect(ctx context.Context, cfg Config) (*Reader, *redis.Client, error) {
	opts, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		return nil, nil, fmt.Errorf("parse redis url: %w", err)
	}
	rdb := redis.NewClient(opts)

	// Make sure the stream itself is addressable. MKSTREAM in XGROUP handles
	// the case where the stream doesn't exist yet.
	err = rdb.XGroupCreateMkStream(ctx, cfg.Stream, cfg.Group, "$").Err()
	if err != nil && !isBusyGroupErr(err) {
		_ = rdb.Close()
		return nil, nil, fmt.Errorf("create consumer group: %w", err)
	}

	log := cfg.Logger
	if log == nil {
		log = slog.Default()
	}
	claimEvery := cfg.ClaimEvery
	if claimEvery <= 0 {
		claimEvery = 30 * time.Second
	}

	return &Reader{
		rdb:        rdb,
		stream:     cfg.Stream,
		group:      cfg.Group,
		consumer:   cfg.Consumer,
		claimIdle:  cfg.ClaimIdle,
		claimEvery: claimEvery,
		logger:     log,
	}, rdb, nil
}

// Read polls the stream for new entries for up to `block`, returning up to
// `count` decoded messages. If a claim window has elapsed we first harvest
// pending entries from dead consumers.
func (r *Reader) Read(ctx context.Context, count int, block time.Duration) ([]pipeline.StreamMessage, error) {
	r.maybeClaim(ctx)

	entries, err := r.rdb.XReadGroup(ctx, &redis.XReadGroupArgs{
		Group:    r.group,
		Consumer: r.consumer,
		Streams:  []string{r.stream, ">"},
		Count:    int64(count),
		Block:    block,
	}).Result()
	if err != nil {
		if errors.Is(err, redis.Nil) {
			return nil, nil
		}
		return nil, err
	}
	return decode(entries), nil
}

// Ack acknowledges the given stream IDs so they are removed from the pending
// entries list for this consumer group.
func (r *Reader) Ack(ctx context.Context, ids []string) error {
	if len(ids) == 0 {
		return nil
	}
	return r.rdb.XAck(ctx, r.stream, r.group, ids...).Err()
}

func (r *Reader) maybeClaim(ctx context.Context) {
	if r.claimIdle <= 0 {
		return
	}
	now := time.Now()
	if !r.lastClaim.IsZero() && now.Sub(r.lastClaim) < r.claimEvery {
		return
	}
	r.lastClaim = now

	_, _, err := r.rdb.XAutoClaim(ctx, &redis.XAutoClaimArgs{
		Stream:   r.stream,
		Group:    r.group,
		Consumer: r.consumer,
		MinIdle:  r.claimIdle,
		Start:    "0-0",
		Count:    256,
	}).Result()
	if err != nil && !errors.Is(err, redis.Nil) {
		r.logger.Warn("events.autoclaim_failed", "err", err)
	}
}

func decode(streams []redis.XStream) []pipeline.StreamMessage {
	out := make([]pipeline.StreamMessage, 0)
	for _, s := range streams {
		for _, m := range s.Messages {
			payload, _ := m.Values["payload"].(string)
			out = append(out, pipeline.StreamMessage{
				ID:      m.ID,
				Payload: []byte(payload),
			})
		}
	}
	return out
}

func isBusyGroupErr(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(err.Error(), "BUSYGROUP")
}
