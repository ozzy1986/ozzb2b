// Package gateway exposes the HTTP entrypoints for the chat service:
//
//	GET /health    — liveness probe, no deps
//	GET /ready     — checks that Redis is reachable
//	GET /ws        — upgrades to a WebSocket that forwards fan-out messages
//
// The WS endpoint is receive-only by design: the browser sends messages via
// the HTTPS API, which persists them and publishes to Redis; the gateway only
// fans them out. This keeps the Go service tiny and moves business logic to
// the single source of truth (the API).
package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"time"

	"github.com/coder/websocket"

	"github.com/ozzy1986/ozzb2b/apps/chat/internal/authz"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/config"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/metrics"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/pubsub"
)

// Handler wires together verifier, pubsub factory and config.
type Handler struct {
	Cfg       *config.Config
	Verifier  *authz.Verifier
	PubSub    pubsub.Factory
	Logger    *slog.Logger
	NowFn     func() time.Time
	ServiceID string
}

// Register attaches every HTTP route on the supplied mux.
func (h *Handler) Register(mux *http.ServeMux) {
	mux.HandleFunc("/health", h.health)
	mux.HandleFunc("/ready", h.ready)
	mux.HandleFunc("/ws", h.websocket)
}

type healthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
	Version string `json:"version"`
}

func (h *Handler) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, healthResponse{Status: "ok", Service: h.ServiceID, Version: h.Cfg.Version})
}

func (h *Handler) ready(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	if err := h.PubSub.Ping(ctx); err != nil {
		writeJSON(w, http.StatusServiceUnavailable, healthResponse{
			Status:  "redis_unavailable",
			Service: h.ServiceID,
			Version: h.Cfg.Version,
		})
		return
	}
	writeJSON(w, http.StatusOK, healthResponse{Status: "ok", Service: h.ServiceID, Version: h.Cfg.Version})
}

// websocket upgrades the HTTP connection and forwards every Redis message for
// the client's conversation to the socket. It never reads business data from
// the browser: it only processes keepalive ping/pong so a disconnected client
// is detected quickly.
func (h *Handler) websocket(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	claims, err := h.Verifier.Parse(token)
	if err != nil {
		metrics.WSConnections.WithLabelValues("auth_failed").Inc()
		h.Logger.Info("ws.auth_failed", "err", err)
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}

	conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{
		OriginPatterns: h.Cfg.AllowedOrigins,
	})
	if err != nil {
		metrics.WSConnections.WithLabelValues("accept_failed").Inc()
		h.Logger.Info("ws.accept_failed", "err", err)
		return
	}
	metrics.WSConnections.WithLabelValues("open").Inc()
	defer conn.Close(websocket.StatusNormalClosure, "bye")

	// Tight bound on any client-sent frame — defense-in-depth, we never expect
	// real payloads from the browser.
	conn.SetReadLimit(h.Cfg.MaxClientMessage)

	// We cap the total session length at the claims' expiry + a margin: a
	// client that refuses to reconnect keeps its token implicitly bound.
	now := h.NowFn()
	deadline := claims.ExpiresAt.Add(1 * time.Hour)
	if !deadline.After(now) {
		h.Logger.Info("ws.token_already_expired", "conv", claims.ConversationID)
		return
	}
	ctx, cancel := context.WithDeadline(r.Context(), deadline)
	defer cancel()

	channel := "chat:conv:" + claims.ConversationID
	sub, err := h.PubSub.Subscribe(ctx, channel)
	if err != nil {
		metrics.RedisSubscribeErrors.Inc()
		h.Logger.Error("ws.subscribe_failed", "err", err, "channel", channel)
		return
	}
	defer func() { _ = sub.Close() }()

	h.Logger.Info("ws.open", "user", claims.UserID, "conv", claims.ConversationID)
	defer h.Logger.Info("ws.close", "user", claims.UserID, "conv", claims.ConversationID)

	// Drain inbound frames so we notice disconnects promptly. We discard the
	// payload: the API is the single writer.
	readErr := make(chan error, 1)
	go func() {
		for {
			if _, _, err := conn.Read(ctx); err != nil {
				readErr <- err
				return
			}
		}
	}()

	pingTicker := time.NewTicker(h.Cfg.PingInterval)
	defer pingTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case err := <-readErr:
			if !isNormalClose(err) {
				h.Logger.Info("ws.client_error", "err", err)
			}
			return
		case <-pingTicker.C:
			pingCtx, pingCancel := context.WithTimeout(ctx, 5*time.Second)
			err := conn.Ping(pingCtx)
			pingCancel()
			if err != nil {
				h.Logger.Info("ws.ping_failed", "err", err)
				return
			}
		case msg, ok := <-sub.Channel():
			if !ok {
				return
			}
			writeCtx, writeCancel := context.WithTimeout(ctx, h.Cfg.WriteTimeout)
			err := conn.Write(writeCtx, websocket.MessageText, []byte(msg.Payload))
			writeCancel()
			if err != nil {
				h.Logger.Info("ws.write_failed", "err", err)
				return
			}
			metrics.WSMessagesForwarded.Inc()
		}
	}
}

func isNormalClose(err error) bool {
	if err == nil {
		return true
	}
	var ce websocket.CloseError
	if errors.As(err, &ce) {
		return ce.Code == websocket.StatusNormalClosure || ce.Code == websocket.StatusGoingAway
	}
	return errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded)
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
