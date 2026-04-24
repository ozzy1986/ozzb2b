package gateway

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"

	"github.com/coder/websocket"
	"github.com/golang-jwt/jwt/v5"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/authz"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/config"
	"github.com/ozzy1986/ozzb2b/apps/chat/internal/pubsub"
)

const testSecret = "this-is-a-32-byte-test-secret!!!"

func newTestServer(t *testing.T, ps pubsub.Factory) (*httptest.Server, *Handler) {
	t.Helper()
	v, err := authz.NewVerifier(testSecret, "HS256")
	if err != nil {
		t.Fatalf("verifier: %v", err)
	}
	h := &Handler{
		Cfg: &config.Config{
			HTTPAddr:         ":0",
			AllowedOrigins:   []string{"*"},
			PingInterval:     100 * time.Millisecond,
			WriteTimeout:     time.Second,
			MaxClientMessage: 1024,
			Version:          "test",
		},
		Verifier:  v,
		PubSub:    ps,
		Logger:    slog.New(slog.NewTextHandler(io.Discard, nil)),
		NowFn:     time.Now,
		ServiceID: "ozzb2b-chat-test",
	}
	mux := http.NewServeMux()
	h.Register(mux)
	return httptest.NewServer(mux), h
}

func validToken(t *testing.T, userID, convID string) string {
	t.Helper()
	claims := jwt.MapClaims{
		"sub": userID,
		"conv": convID,
		"typ": "ws_chat",
		"iat": time.Now().Add(-time.Second).Unix(),
		"exp": time.Now().Add(2 * time.Minute).Unix(),
		"jti": "t",
	}
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	s, err := tok.SignedString([]byte(testSecret))
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	return s
}

func TestHealth(t *testing.T) {
	ps := pubsub.NewMemoryFactory()
	srv, _ := newTestServer(t, ps)
	defer srv.Close()
	resp, err := http.Get(srv.URL + "/health")
	if err != nil {
		t.Fatalf("health: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status=%d", resp.StatusCode)
	}
	var body struct{ Status, Service, Version string }
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if body.Status != "ok" {
		t.Fatalf("expected ok, got %s", body.Status)
	}
}

func TestReady(t *testing.T) {
	ps := pubsub.NewMemoryFactory()
	srv, _ := newTestServer(t, ps)
	defer srv.Close()
	resp, err := http.Get(srv.URL + "/ready")
	if err != nil {
		t.Fatalf("ready: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status=%d", resp.StatusCode)
	}
}

func TestWebsocket_RejectsInvalidToken(t *testing.T) {
	ps := pubsub.NewMemoryFactory()
	srv, _ := newTestServer(t, ps)
	defer srv.Close()
	resp, err := http.Get(srv.URL + "/ws?token=bad")
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusUnauthorized {
		t.Fatalf("status=%d", resp.StatusCode)
	}
}

func TestWebsocket_ForwardsPublishedMessage(t *testing.T) {
	ps := pubsub.NewMemoryFactory()
	srv, _ := newTestServer(t, ps)
	defer srv.Close()

	wsURL := strings.Replace(srv.URL, "http://", "ws://", 1)
	u, _ := url.Parse(wsURL + "/ws")
	q := u.Query()
	q.Set("token", validToken(t, "u-1", "conv-1"))
	u.RawQuery = q.Encode()

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	conn, _, err := websocket.Dial(ctx, u.String(), nil)
	if err != nil {
		t.Fatalf("dial: %v", err)
	}
	defer conn.Close(websocket.StatusNormalClosure, "bye")

	// Give the server a moment to register the subscription.
	time.Sleep(100 * time.Millisecond)
	ps.Publish("chat:conv:conv-1", `{"id":"m1","body":"hi"}`)

	readCtx, readCancel := context.WithTimeout(ctx, 2*time.Second)
	defer readCancel()
	typ, data, err := conn.Read(readCtx)
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if typ != websocket.MessageText {
		t.Fatalf("unexpected type: %v", typ)
	}
	if string(data) != `{"id":"m1","body":"hi"}` {
		t.Fatalf("unexpected payload: %s", string(data))
	}
}
