// Package config loads the chat gateway's runtime configuration from env vars.
// We keep configuration immutable after startup: callers must request a fresh
// Config via Load() and never mutate the returned value.
package config

import (
	"errors"
	"os"
	"strings"
	"time"
)

const (
	// tokenTypeWsChat must match the value issued by the API
	// (security/tokens.py TOKEN_TYPE_WS_CHAT).
	TokenTypeWsChat = "ws_chat"

	defaultHTTPAddr         = ":8090"
	defaultAllowedOrigins   = "https://ozzb2b.com,https://www.ozzb2b.com"
	defaultRedisURL         = "redis://localhost:6379/3"
	defaultReadTimeout      = 30 * time.Second
	defaultWriteTimeout     = 30 * time.Second
	defaultIdleTimeout      = 60 * time.Second
	defaultPingInterval     = 30 * time.Second
	defaultPongWait         = 60 * time.Second
	defaultMaxClientMessage = 4 * 1024
)

// Config is the frozen configuration snapshot used by the gateway.
type Config struct {
	HTTPAddr         string
	JWTSecret        string
	JWTAlgorithm     string
	RedisURL         string
	AllowedOrigins   []string
	ReadTimeout      time.Duration
	WriteTimeout     time.Duration
	IdleTimeout      time.Duration
	PingInterval     time.Duration
	PongWait         time.Duration
	MaxClientMessage int64
	Version          string
}

// Load reads the configuration from the environment. It returns an error when
// a required value is missing so the gateway fails fast on misconfiguration.
func Load(version string) (*Config, error) {
	secret := os.Getenv("OZZB2B_JWT_SECRET")
	if strings.TrimSpace(secret) == "" {
		return nil, errors.New("OZZB2B_JWT_SECRET is required")
	}
	cfg := &Config{
		HTTPAddr:         envOr("OZZB2B_CHAT_HTTP_ADDR", defaultHTTPAddr),
		JWTSecret:        secret,
		JWTAlgorithm:     envOr("OZZB2B_JWT_ALGORITHM", "HS256"),
		RedisURL:         envOr("OZZB2B_REDIS_URL", defaultRedisURL),
		AllowedOrigins:   splitCSV(envOr("OZZB2B_CHAT_ALLOWED_ORIGINS", defaultAllowedOrigins)),
		ReadTimeout:      defaultReadTimeout,
		WriteTimeout:     defaultWriteTimeout,
		IdleTimeout:      defaultIdleTimeout,
		PingInterval:     defaultPingInterval,
		PongWait:         defaultPongWait,
		MaxClientMessage: defaultMaxClientMessage,
		Version:          version,
	}
	return cfg, nil
}

func envOr(key, def string) string {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		return v
	}
	return def
}

func splitCSV(s string) []string {
	raw := strings.Split(s, ",")
	out := make([]string, 0, len(raw))
	for _, v := range raw {
		v = strings.TrimSpace(v)
		if v != "" {
			out = append(out, v)
		}
	}
	return out
}
