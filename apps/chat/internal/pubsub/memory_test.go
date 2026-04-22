package pubsub

import (
	"context"
	"testing"
	"time"
)

func TestMemoryFactory_PublishDelivers(t *testing.T) {
	f := NewMemoryFactory()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sub, err := f.Subscribe(ctx, "conv:1")
	if err != nil {
		t.Fatalf("subscribe: %v", err)
	}
	defer sub.Close()

	go f.Publish("conv:1", "hello")

	select {
	case msg := <-sub.Channel():
		if msg.Channel != "conv:1" || msg.Payload != "hello" {
			t.Fatalf("unexpected: %+v", msg)
		}
	case <-time.After(time.Second):
		t.Fatalf("timeout waiting for message")
	}
}

func TestMemoryFactory_PublishIsolatedPerChannel(t *testing.T) {
	f := NewMemoryFactory()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sub, _ := f.Subscribe(ctx, "conv:1")
	defer sub.Close()

	f.Publish("conv:2", "other")

	select {
	case msg := <-sub.Channel():
		t.Fatalf("must not deliver cross-channel: %+v", msg)
	case <-time.After(50 * time.Millisecond):
		// expected: no delivery
	}
}
