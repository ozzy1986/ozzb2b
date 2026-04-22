// Package pubsub abstracts the message transport between the API (writer)
// and the WebSocket gateway (reader). The gateway subscribes to a channel
// per conversation and forwards raw payloads to the attached WS client.
//
// The Subscriber interface lets us swap the Redis client for an in-memory
// fake in unit tests without touching the rest of the code.
package pubsub

import (
	"context"

	"github.com/redis/go-redis/v9"
)

// Subscriber lets callers listen to one or more channels and consume the
// delivered payloads. `Close()` releases any resources.
type Subscriber interface {
	Channel() <-chan Message
	Close() error
}

// Message is the normalised payload delivered to subscribers.
type Message struct {
	Channel string
	Payload string
}

// Factory builds a new Subscriber for the given channel names.
// Returning an interface (not a concrete type) lets us mock it in tests.
type Factory interface {
	Subscribe(ctx context.Context, channels ...string) (Subscriber, error)
	Ping(ctx context.Context) error
	Close() error
}

// RedisFactory wraps a go-redis client and produces redis-backed subscribers.
type RedisFactory struct {
	client *redis.Client
}

// NewRedisFactory connects to Redis using the provided URL.
func NewRedisFactory(url string) (*RedisFactory, error) {
	opt, err := redis.ParseURL(url)
	if err != nil {
		return nil, err
	}
	return &RedisFactory{client: redis.NewClient(opt)}, nil
}

// Subscribe returns a Subscriber that receives messages on the given channels.
func (f *RedisFactory) Subscribe(ctx context.Context, channels ...string) (Subscriber, error) {
	ps := f.client.Subscribe(ctx, channels...)
	// Block until the subscription is acknowledged so the caller knows the
	// gateway will actually receive new messages published after this call.
	if _, err := ps.Receive(ctx); err != nil {
		_ = ps.Close()
		return nil, err
	}
	return &redisSubscriber{ps: ps, ch: adapt(ps.Channel())}, nil
}

// Ping validates the connection to Redis (used by `/ready`).
func (f *RedisFactory) Ping(ctx context.Context) error {
	return f.client.Ping(ctx).Err()
}

// Close releases the underlying client.
func (f *RedisFactory) Close() error {
	return f.client.Close()
}

type redisSubscriber struct {
	ps *redis.PubSub
	ch <-chan Message
}

func (s *redisSubscriber) Channel() <-chan Message { return s.ch }

func (s *redisSubscriber) Close() error {
	return s.ps.Close()
}

// adapt converts a redis-specific channel into the transport-neutral shape.
func adapt(in <-chan *redis.Message) <-chan Message {
	out := make(chan Message, 32)
	go func() {
		defer close(out)
		for m := range in {
			out <- Message{Channel: m.Channel, Payload: m.Payload}
		}
	}()
	return out
}
