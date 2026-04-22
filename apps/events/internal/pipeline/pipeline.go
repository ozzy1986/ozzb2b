// Package pipeline wires a Redis Streams reader to a ClickHouse batch writer.
//
// Design notes:
// - The stream reader and the writer are small interfaces so we can mock
//   both in tests. `Run` is the only public surface and is a thin loop.
// - On any writer failure we never ACK: the messages stay "pending" for the
//   consumer group and will be redelivered next cycle. This costs some
//   duplicate inserts on flaky networks (ClickHouse dedups via ReplacingMT
//   in the future) but keeps the path at-least-once with no data loss.
// - We XAUTOCLAIM idle messages so a crashed consumer does not permanently
//   leave events pending. Best-effort, logged on failure.
package pipeline

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"time"

	"github.com/ozzy1986/ozzb2b/apps/events/internal/clickhouse"
)

// StreamMessage is a single Redis Stream entry after decoding.
type StreamMessage struct {
	ID      string
	Payload []byte
}

// StreamReader is the subset of a Redis Streams client the pipeline needs.
type StreamReader interface {
	Read(ctx context.Context, count int, block time.Duration) ([]StreamMessage, error)
	Ack(ctx context.Context, ids []string) error
}

// Writer persists a batch of ClickHouse rows.
type Writer interface {
	InsertRows(ctx context.Context, rows []clickhouse.Row) (int, error)
}

type Config struct {
	BatchSize     int
	FlushInterval time.Duration
	Logger        *slog.Logger
}

// Envelope mirrors the JSON published by the API's EventEmitter.
type Envelope struct {
	EventID    string          `json:"event_id"`
	EventType  string          `json:"event_type"`
	OccurredAt string          `json:"occurred_at"`
	UserID     *string         `json:"user_id"`
	SessionID  *string         `json:"session_id"`
	Properties json.RawMessage `json:"properties"`
}

// Run reads messages from `r`, converts them to ClickHouse rows and calls
// `w.InsertRows`. It returns when the context is cancelled.
func Run(ctx context.Context, r StreamReader, w Writer, cfg Config) error {
	log := cfg.Logger
	if log == nil {
		log = slog.Default()
	}
	batch := cfg.BatchSize
	if batch < 1 {
		batch = 200
	}
	block := cfg.FlushInterval
	if block <= 0 {
		block = 500 * time.Millisecond
	}

	for {
		if err := ctx.Err(); err != nil {
			return err
		}

		msgs, err := r.Read(ctx, batch, block)
		if err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return err
			}
			log.Warn("events.read_failed", "err", err)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(time.Second):
			}
			continue
		}
		if len(msgs) == 0 {
			continue
		}

		rows, ids := convert(msgs, log)
		if len(rows) == 0 {
			// Nothing parseable — still ACK to drain the poison pill.
			if err := r.Ack(ctx, ids); err != nil {
				log.Warn("events.ack_failed", "err", err, "count", len(ids))
			}
			continue
		}

		n, err := w.InsertRows(ctx, rows)
		if err != nil {
			log.Warn("events.insert_failed", "err", err, "rows", len(rows))
			continue
		}

		if err := r.Ack(ctx, ids); err != nil {
			log.Warn("events.ack_failed", "err", err, "count", len(ids))
			continue
		}

		log.Info("events.batch_inserted", "rows", n, "ids", len(ids))
	}
}

// convert turns raw stream messages into ClickHouse rows. Unparseable
// envelopes are dropped but their stream IDs are still returned so callers
// can ACK them and keep the stream moving.
func convert(msgs []StreamMessage, log *slog.Logger) (rows []clickhouse.Row, ids []string) {
	rows = make([]clickhouse.Row, 0, len(msgs))
	ids = make([]string, 0, len(msgs))
	for _, m := range msgs {
		ids = append(ids, m.ID)
		var env Envelope
		if err := json.Unmarshal(m.Payload, &env); err != nil {
			log.Warn("events.bad_envelope", "err", err, "id", m.ID)
			continue
		}
		if env.EventID == "" || env.EventType == "" || env.OccurredAt == "" {
			log.Warn("events.missing_fields", "id", m.ID)
			continue
		}
		props := string(env.Properties)
		if props == "" {
			props = "{}"
		}
		rows = append(rows, clickhouse.Row{
			EventID:    env.EventID,
			EventType:  env.EventType,
			OccurredAt: env.OccurredAt,
			UserID:     env.UserID,
			SessionID:  env.SessionID,
			Properties: props,
		})
	}
	return rows, ids
}
