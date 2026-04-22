// Package config loads the events consumer's runtime configuration from env
// vars. Config is captured once at startup and passed around as an immutable
// value object.
package config

import (
	"errors"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	HTTPAddr string

	RedisURL    string
	StreamName  string
	GroupName   string
	ConsumerID  string
	ClaimIdleMs time.Duration

	BatchSize     int
	FlushInterval time.Duration

	ClickhouseURL      string
	ClickhouseUser     string
	ClickhousePassword string
	ClickhouseDatabase string
	ClickhouseTimeout  time.Duration

	DisablePipeline bool

	Version string
}

func Load(version string) (*Config, error) {
	cfg := &Config{
		HTTPAddr:    envOr("OZZB2B_EVENTS_HTTP_ADDR", ":8095"),
		RedisURL:    envOr("OZZB2B_REDIS_URL", "redis://localhost:6379/3"),
		StreamName:  envOr("OZZB2B_EVENTS_STREAM", "ozzb2b:events:v1"),
		GroupName:   envOr("OZZB2B_EVENTS_GROUP", "events-to-clickhouse"),
		ConsumerID:  envOr("OZZB2B_EVENTS_CONSUMER", defaultConsumerID()),
		ClaimIdleMs: envDuration("OZZB2B_EVENTS_CLAIM_IDLE_MS", 60*time.Second),

		BatchSize:     envInt("OZZB2B_EVENTS_BATCH_SIZE", 200),
		FlushInterval: envDuration("OZZB2B_EVENTS_FLUSH_MS", 500*time.Millisecond),

		ClickhouseURL:      envOr("OZZB2B_CLICKHOUSE_URL", "http://clickhouse:8123"),
		ClickhouseUser:     envOr("OZZB2B_CLICKHOUSE_USER", "default"),
		ClickhousePassword: os.Getenv("OZZB2B_CLICKHOUSE_PASSWORD"),
		ClickhouseDatabase: envOr("OZZB2B_CLICKHOUSE_DATABASE", "ozzb2b"),
		ClickhouseTimeout:  envDuration("OZZB2B_CLICKHOUSE_TIMEOUT_MS", 5*time.Second),

		DisablePipeline: envBool("OZZB2B_EVENTS_DISABLE_PIPELINE", false),

		Version: version,
	}

	if cfg.BatchSize < 1 {
		return nil, errors.New("OZZB2B_EVENTS_BATCH_SIZE must be positive")
	}
	return cfg, nil
}

func envOr(key, def string) string {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		return v
	}
	return def
}

func envInt(key string, def int) int {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def
	}
	i, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return i
}

func envBool(key string, def bool) bool {
	v := strings.ToLower(strings.TrimSpace(os.Getenv(key)))
	if v == "" {
		return def
	}
	switch v {
	case "1", "true", "yes", "on":
		return true
	case "0", "false", "no", "off":
		return false
	}
	return def
}

func envDuration(key string, def time.Duration) time.Duration {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def
	}
	// Support raw milliseconds as integers (`500`) or Go durations (`500ms`).
	if d, err := time.ParseDuration(v); err == nil {
		return d
	}
	if i, err := strconv.Atoi(v); err == nil {
		return time.Duration(i) * time.Millisecond
	}
	return def
}

func defaultConsumerID() string {
	host, err := os.Hostname()
	if err != nil || host == "" {
		return "events-1"
	}
	return host
}
