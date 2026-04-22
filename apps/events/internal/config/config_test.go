package config

import (
	"testing"
	"time"
)

func TestLoadDefaults(t *testing.T) {
	t.Setenv("OZZB2B_REDIS_URL", "redis://localhost:6379/0")
	t.Setenv("OZZB2B_EVENTS_HTTP_ADDR", "")
	t.Setenv("OZZB2B_CLICKHOUSE_URL", "")

	cfg, err := Load("test")
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.HTTPAddr != ":8095" {
		t.Fatalf("default HTTPAddr, got %q", cfg.HTTPAddr)
	}
	if cfg.StreamName != "ozzb2b:events:v1" {
		t.Fatalf("default stream, got %q", cfg.StreamName)
	}
	if cfg.BatchSize != 200 {
		t.Fatalf("default batch size, got %d", cfg.BatchSize)
	}
	if cfg.FlushInterval != 500*time.Millisecond {
		t.Fatalf("default flush, got %s", cfg.FlushInterval)
	}
	if cfg.ClickhouseDatabase != "ozzb2b" {
		t.Fatalf("default db, got %q", cfg.ClickhouseDatabase)
	}
}

func TestLoadFailsOnInvalidBatch(t *testing.T) {
	t.Setenv("OZZB2B_EVENTS_BATCH_SIZE", "0")
	_, err := Load("test")
	if err == nil {
		t.Fatal("expected error when batch size is non-positive")
	}
}

func TestEnvDurationAcceptsMillisOrGoFormat(t *testing.T) {
	t.Setenv("OZZB2B_REDIS_URL", "redis://localhost:6379/0")
	t.Setenv("OZZB2B_EVENTS_FLUSH_MS", "250")
	cfg, err := Load("test")
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.FlushInterval != 250*time.Millisecond {
		t.Fatalf("expected 250ms, got %s", cfg.FlushInterval)
	}

	t.Setenv("OZZB2B_EVENTS_FLUSH_MS", "1s")
	cfg, err = Load("test")
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.FlushInterval != time.Second {
		t.Fatalf("expected 1s, got %s", cfg.FlushInterval)
	}
}
