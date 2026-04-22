package clickhouse

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestInsertRowsSendsJSONEachRow(t *testing.T) {
	var (
		gotPath        string
		gotQuery       string
		gotBody        []byte
		gotAuthUser    string
		gotAuthHasAuth bool
	)

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotQuery = r.URL.RawQuery
		gotAuthUser, _, gotAuthHasAuth = r.BasicAuth()
		body, _ := io.ReadAll(r.Body)
		gotBody = body
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	c := New(Config{
		BaseURL:  srv.URL,
		Database: "ozzb2b",
		User:     "default",
		Password: "",
		Timeout:  2 * time.Second,
	})

	session := "sid-1"
	rows := []Row{
		{EventID: "e1", EventType: "search_performed", OccurredAt: "2026-04-22T10:00:00Z", SessionID: &session, Properties: `{"query":"q"}`},
		{EventID: "e2", EventType: "provider_viewed", OccurredAt: "2026-04-22T10:00:01Z", Properties: `{"slug":"agima"}`},
	}

	n, err := c.InsertRows(context.Background(), rows)
	if err != nil {
		t.Fatalf("InsertRows: %v", err)
	}
	if n != 2 {
		t.Fatalf("expected 2 rows inserted, got %d", n)
	}
	if gotPath != "/" {
		t.Fatalf("unexpected path %q", gotPath)
	}
	if !strings.Contains(gotQuery, "database=ozzb2b") {
		t.Fatalf("missing database param: %s", gotQuery)
	}
	if !strings.Contains(gotQuery, "query=INSERT") {
		t.Fatalf("missing query param: %s", gotQuery)
	}
	if !strings.Contains(gotQuery, "date_time_input_format=best_effort") {
		t.Fatalf("expected best_effort datetime setting, got: %s", gotQuery)
	}
	// Body must be newline-delimited JSON objects.
	lines := bytes.Split(bytes.TrimRight(gotBody, "\n"), []byte("\n"))
	if len(lines) != 2 {
		t.Fatalf("expected 2 lines, got %d (body=%q)", len(lines), gotBody)
	}
	var back Row
	if err := json.Unmarshal(lines[0], &back); err != nil {
		t.Fatalf("decode row: %v", err)
	}
	if back.EventID != "e1" {
		t.Fatalf("expected e1, got %s", back.EventID)
	}
	if !gotAuthHasAuth || gotAuthUser != "default" {
		t.Fatalf("expected basic auth with default user")
	}
}

func TestInsertRowsPropagatesError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte("bad"))
	}))
	defer srv.Close()

	c := New(Config{BaseURL: srv.URL, Database: "ozzb2b", Timeout: time.Second})
	_, err := c.InsertRows(context.Background(), []Row{{EventID: "e1"}})
	if err == nil {
		t.Fatal("expected error on non-2xx response")
	}
	if !strings.Contains(err.Error(), "status=400") {
		t.Fatalf("expected status in error, got %v", err)
	}
}

func TestInsertRowsNoopOnEmptyBatch(t *testing.T) {
	c := New(Config{BaseURL: "http://not-used", Database: "ozzb2b", Timeout: time.Second})
	n, err := c.InsertRows(context.Background(), nil)
	if err != nil {
		t.Fatalf("InsertRows: %v", err)
	}
	if n != 0 {
		t.Fatalf("expected zero rows, got %d", n)
	}
}
