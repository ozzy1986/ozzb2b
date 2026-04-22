package pubsub

import (
	"context"
	"sync"
)

// MemorySubscriber is a test-only in-memory Subscriber.
// Use NewMemoryFactory in tests to avoid depending on a real Redis.
type MemorySubscriber struct {
	ch     chan Message
	closed chan struct{}
	once   sync.Once
}

// Publish delivers a payload to all active subscribers of the same channel.
// In-memory, the mapping from channel name to subscriber is kept in a single
// shared map owned by the factory.
func (s *MemorySubscriber) Publish(msg Message) {
	select {
	case <-s.closed:
	case s.ch <- msg:
	}
}

func (s *MemorySubscriber) Channel() <-chan Message { return s.ch }

func (s *MemorySubscriber) Close() error {
	s.once.Do(func() {
		close(s.closed)
		close(s.ch)
	})
	return nil
}

// MemoryFactory is a Factory that keeps subscribers in a map. Only intended
// for tests; it is safe for concurrent use.
type MemoryFactory struct {
	mu   sync.Mutex
	subs map[string][]*MemorySubscriber
}

func NewMemoryFactory() *MemoryFactory {
	return &MemoryFactory{subs: make(map[string][]*MemorySubscriber)}
}

func (f *MemoryFactory) Subscribe(ctx context.Context, channels ...string) (Subscriber, error) {
	sub := &MemorySubscriber{
		ch:     make(chan Message, 16),
		closed: make(chan struct{}),
	}
	f.mu.Lock()
	for _, c := range channels {
		f.subs[c] = append(f.subs[c], sub)
	}
	f.mu.Unlock()
	go func() {
		<-ctx.Done()
		_ = sub.Close()
	}()
	return sub, nil
}

func (f *MemoryFactory) Publish(channel, payload string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	for _, s := range f.subs[channel] {
		s.Publish(Message{Channel: channel, Payload: payload})
	}
}

func (f *MemoryFactory) Ping(ctx context.Context) error { return nil }
func (f *MemoryFactory) Close() error                   { return nil }
