package pipeline

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"sync"
	"testing"
	"time"

	"github.com/ozzy1986/ozzb2b/apps/events/internal/clickhouse"
)

type fakeReader struct {
	mu        sync.Mutex
	batches   [][]StreamMessage
	acked     [][]string
	readErr   error
	done      chan struct{}
	returnAll bool
}

func (f *fakeReader) Read(ctx context.Context, _ int, _ time.Duration) ([]StreamMessage, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if f.readErr != nil {
		return nil, f.readErr
	}
	if len(f.batches) == 0 {
		if f.returnAll {
			close(f.done)
			f.returnAll = false
		}
		return nil, nil
	}
	batch := f.batches[0]
	f.batches = f.batches[1:]
	return batch, nil
}

func (f *fakeReader) Ack(_ context.Context, ids []string) error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.acked = append(f.acked, ids)
	return nil
}

type fakeWriter struct {
	mu        sync.Mutex
	rows      []clickhouse.Row
	err       error
	callCount int
}

func (w *fakeWriter) InsertRows(_ context.Context, rows []clickhouse.Row) (int, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.callCount++
	if w.err != nil {
		return 0, w.err
	}
	w.rows = append(w.rows, rows...)
	return len(rows), nil
}

func newDiscardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func mustMarshal(t *testing.T, env Envelope) []byte {
	t.Helper()
	b, err := json.Marshal(env)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	return b
}

func TestRunHappyPath(t *testing.T) {
	user := "u-1"
	msgs := []StreamMessage{
		{ID: "1-0", Payload: mustMarshal(t, Envelope{
			EventID:    "e1",
			EventType:  "search_performed",
			OccurredAt: "2026-04-22T10:00:00Z",
			UserID:     &user,
			Properties: json.RawMessage(`{"query":"q"}`),
		})},
		{ID: "2-0", Payload: mustMarshal(t, Envelope{
			EventID:    "e2",
			EventType:  "provider_viewed",
			OccurredAt: "2026-04-22T10:00:01Z",
			Properties: json.RawMessage(`{"slug":"agima"}`),
		})},
	}
	reader := &fakeReader{batches: [][]StreamMessage{msgs}, done: make(chan struct{}), returnAll: true}
	writer := &fakeWriter{}

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	done := make(chan error, 1)
	go func() { done <- Run(ctx, reader, writer, Config{BatchSize: 10, FlushInterval: 10 * time.Millisecond, Logger: newDiscardLogger()}) }()

	select {
	case <-reader.done:
	case <-time.After(300 * time.Millisecond):
		t.Fatal("reader did not drain in time")
	}
	cancel()
	<-done

	if len(writer.rows) != 2 {
		t.Fatalf("expected 2 rows written, got %d", len(writer.rows))
	}
	if len(reader.acked) != 1 || len(reader.acked[0]) != 2 {
		t.Fatalf("expected 2 ids acked, got %v", reader.acked)
	}
	if writer.rows[0].EventID != "e1" {
		t.Fatalf("unexpected first row: %+v", writer.rows[0])
	}
}

func TestRunDoesNotAckOnWriteFailure(t *testing.T) {
	msgs := []StreamMessage{
		{ID: "1-0", Payload: mustMarshal(t, Envelope{
			EventID:    "e1",
			EventType:  "search_performed",
			OccurredAt: "2026-04-22T10:00:00Z",
			Properties: json.RawMessage(`{}`),
		})},
	}
	reader := &fakeReader{batches: [][]StreamMessage{msgs}, done: make(chan struct{}), returnAll: true}
	writer := &fakeWriter{err: errors.New("boom")}

	ctx, cancel := context.WithTimeout(context.Background(), 400*time.Millisecond)
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- Run(ctx, reader, writer, Config{BatchSize: 10, FlushInterval: 10 * time.Millisecond, Logger: newDiscardLogger()}) }()

	select {
	case <-reader.done:
	case <-time.After(300 * time.Millisecond):
	}
	cancel()
	<-done

	if len(reader.acked) != 0 {
		t.Fatalf("ack must not fire on write failure, got %v", reader.acked)
	}
}

func TestConvertDropsBadEnvelopesButStillAcks(t *testing.T) {
	msgs := []StreamMessage{
		{ID: "1-0", Payload: []byte("not-json")},
		{ID: "2-0", Payload: mustMarshal(t, Envelope{
			EventID:    "e1",
			EventType:  "search_performed",
			OccurredAt: "2026-04-22T10:00:00Z",
			Properties: json.RawMessage(`{"query":"q"}`),
		})},
		{ID: "3-0", Payload: mustMarshal(t, Envelope{EventID: "", EventType: "", OccurredAt: ""})},
	}
	rows, ids := convert(msgs, newDiscardLogger())
	if len(rows) != 1 || rows[0].EventID != "e1" {
		t.Fatalf("expected single valid row, got %+v", rows)
	}
	if len(ids) != 3 {
		t.Fatalf("expected all 3 ids to be acked, got %v", ids)
	}
}
