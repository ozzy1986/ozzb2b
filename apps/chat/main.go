// Package main is the entry point for the ozzb2b chat service.
//
// The service exposes a read-only WebSocket gateway that forwards new chat
// messages from Redis pub/sub to authenticated browsers. All persistence is
// handled by the API: this binary stays intentionally small and stateless so
// it can be horizontally scaled with zero coordination.
package main

import (
	"context"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/ozzy1986/ozzb2b/apps/chat/internal/authz"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/config"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/gateway"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/pubsub"
)

const version = "0.2.0"

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	cfg, err := config.Load(version)
	if err != nil {
		logger.Error("chat.config_error", "err", err)
		os.Exit(1)
	}
	if len(os.Args) > 1 && os.Args[1] == "healthcheck" {
		if err := runHealthcheck(cfg.HTTPAddr); err != nil {
			logger.Error("chat.healthcheck_failed", "err", err)
			os.Exit(1)
		}
		return
	}

	verifier, err := authz.NewVerifier(cfg.JWTSecret, cfg.JWTAlgorithm)
	if err != nil {
		logger.Error("chat.verifier_error", "err", err)
		os.Exit(1)
	}
	if cfg.JWTAudience != "" {
		verifier = verifier.WithAudience(cfg.JWTAudience)
	}
	if cfg.JWTIssuer != "" {
		verifier = verifier.WithIssuer(cfg.JWTIssuer)
	}

	rf, err := pubsub.NewRedisFactory(cfg.RedisURL)
	if err != nil {
		logger.Error("chat.redis_error", "err", err)
		os.Exit(1)
	}
	defer func() { _ = rf.Close() }()

	handler := &gateway.Handler{
		Cfg:       cfg,
		Verifier:  verifier,
		PubSub:    rf,
		Logger:    logger,
		NowFn:     time.Now,
		ServiceID: "ozzb2b-chat",
	}
	mux := http.NewServeMux()
	handler.Register(mux)
	mux.Handle("/metrics", promhttp.Handler())

	srv := &http.Server{
		Addr:              cfg.HTTPAddr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		// Keep read/write timeouts open enough for long-lived WebSockets:
		// the per-frame deadlines are enforced inside the handler.
		ReadTimeout:  0,
		WriteTimeout: 0,
		IdleTimeout:  cfg.IdleTimeout,
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	go func() {
		logger.Info("chat.start", "addr", cfg.HTTPAddr, "version", version)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("chat.listen_error", "err", err)
			stop()
		}
	}()

	<-ctx.Done()
	logger.Info("chat.stop")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		logger.Error("chat.shutdown_error", "err", err)
	}
}

func runHealthcheck(httpAddr string) error {
	hostPort := httpAddr
	if hostPort == "" {
		hostPort = ":8090"
	}
	if host, port, err := net.SplitHostPort(hostPort); err == nil {
		if host == "" {
			host = "127.0.0.1"
		}
		hostPort = net.JoinHostPort(host, port)
	}
	url := "http://" + hostPort + "/health"

	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return errors.New("non-200 health status")
	}
	return nil
}
