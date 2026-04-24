// Package main is the entry point for the ozzb2b events consumer.
//
// The service is stateless: it reads JSON envelopes from a Redis Stream
// (published by the API's `EventEmitter`), converts them into rows and batch-
// inserts them into ClickHouse via the HTTP interface.
//
// HTTP surface:
//   - GET /health — liveness, no deps.
//   - GET /ready  — readiness, touches Redis+ClickHouse.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/redis/go-redis/v9"

	"github.com/ozzy1986/ozzb2b/apps/events/internal/clickhouse"
	"github.com/ozzy1986/ozzb2b/apps/events/internal/config"
	"github.com/ozzy1986/ozzb2b/apps/events/internal/pipeline"
	"github.com/ozzy1986/ozzb2b/apps/events/internal/stream"
)

const version = "0.2.0"

type healthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
	Version string `json:"version"`
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	cfg, err := config.Load(version)
	if err != nil {
		logger.Error("events.config_error", "err", err)
		os.Exit(1)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	ch := clickhouse.New(clickhouse.Config{
		BaseURL:  cfg.ClickhouseURL,
		Database: cfg.ClickhouseDatabase,
		User:     cfg.ClickhouseUser,
		Password: cfg.ClickhousePassword,
		Timeout:  cfg.ClickhouseTimeout,
	})

	// Bootstrap the schema best-effort — retry until ClickHouse becomes
	// reachable or ctx is cancelled. The consumer is useless without a
	// table, so we would rather block here than spin and drop events.
	if !cfg.DisablePipeline {
		if err := waitForBootstrap(ctx, ch, logger); err != nil {
			logger.Error("events.bootstrap_failed", "err", err)
			os.Exit(1)
		}
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, healthResponse{
			Status: "ok", Service: "ozzb2b-events", Version: version,
		})
	})
	mux.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		cctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()
		if err := ch.Bootstrap(cctx); err != nil {
			writeJSON(w, http.StatusServiceUnavailable, healthResponse{
				Status: "clickhouse_unavailable", Service: "ozzb2b-events", Version: version,
			})
			return
		}
		// Stream connectivity matters as much as ClickHouse — a Redis
		// outage stalls the pipeline silently otherwise.
		if err := pingRedis(cctx, cfg.RedisURL); err != nil {
			writeJSON(w, http.StatusServiceUnavailable, healthResponse{
				Status: "redis_unavailable", Service: "ozzb2b-events", Version: version,
			})
			return
		}
		writeJSON(w, http.StatusOK, healthResponse{
			Status: "ok", Service: "ozzb2b-events", Version: version,
		})
	})
	mux.Handle("/metrics", promhttp.Handler())

	srv := &http.Server{
		Addr:              cfg.HTTPAddr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	go func() {
		logger.Info("events.http.start", "addr", cfg.HTTPAddr, "version", version)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("events.http.listen_error", "err", err)
			stop()
		}
	}()

	if !cfg.DisablePipeline {
		go func() {
			if err := runPipeline(ctx, cfg, ch, logger); err != nil && !errors.Is(err, context.Canceled) {
				logger.Error("events.pipeline_exit", "err", err)
				stop()
			}
		}()
	}

	<-ctx.Done()
	logger.Info("events.stop")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdownCtx)
}

func runPipeline(ctx context.Context, cfg *config.Config, w *clickhouse.Client, logger *slog.Logger) error {
	reader, rdb, err := stream.Connect(ctx, stream.Config{
		RedisURL:  cfg.RedisURL,
		Stream:    cfg.StreamName,
		Group:     cfg.GroupName,
		Consumer:  cfg.ConsumerID,
		ClaimIdle: cfg.ClaimIdleMs,
		Logger:    logger,
	})
	if err != nil {
		return err
	}
	defer rdb.Close()

	logger.Info("events.pipeline.start",
		"stream", cfg.StreamName,
		"group", cfg.GroupName,
		"consumer", cfg.ConsumerID,
	)

	return pipeline.Run(ctx, reader, w, pipeline.Config{
		BatchSize:     cfg.BatchSize,
		FlushInterval: cfg.FlushInterval,
		Logger:        logger,
	})
}

func waitForBootstrap(ctx context.Context, ch *clickhouse.Client, logger *slog.Logger) error {
	backoff := time.Second
	for {
		cctx, cancel := context.WithTimeout(ctx, 3*time.Second)
		err := ch.Bootstrap(cctx)
		cancel()
		if err == nil {
			logger.Info("events.bootstrap_ok")
			return nil
		}
		logger.Warn("events.bootstrap_retry", "err", err, "backoff", backoff.String())
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(backoff):
		}
		if backoff < 10*time.Second {
			backoff *= 2
		}
	}
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

// pingRedis opens a short-lived client just for the readiness probe so we
// don't have to thread the pipeline's go-redis client into the HTTP handler.
func pingRedis(ctx context.Context, url string) error {
	opts, err := redis.ParseURL(url)
	if err != nil {
		return err
	}
	c := redis.NewClient(opts)
	defer c.Close()
	return c.Ping(ctx).Err()
}
