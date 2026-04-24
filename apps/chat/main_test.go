package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRunHealthcheckOK(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/health" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	if err := runHealthcheck(srv.Listener.Addr().String()); err != nil {
		t.Fatalf("expected nil error, got: %v", err)
	}
}

func TestRunHealthcheckNon200(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	if err := runHealthcheck(srv.Listener.Addr().String()); err == nil {
		t.Fatal("expected error for non-200 status")
	}
}

func TestRunHealthcheckConnectionError(t *testing.T) {
	if err := runHealthcheck("127.0.0.1:1"); err == nil {
		t.Fatal("expected error for unreachable endpoint")
	}
}
