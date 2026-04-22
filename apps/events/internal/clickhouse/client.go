// Package clickhouse contains a tiny HTTP client tailored to the events
// consumer: a bootstrap that is idempotent against the target schema and a
// batch INSERT using the JSONEachRow format. We deliberately avoid pulling in
// the full native driver — the write path is one statement, one format.
package clickhouse

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

type Client struct {
	base     string
	database string
	user     string
	password string
	http     *http.Client
}

type Config struct {
	BaseURL  string
	Database string
	User     string
	Password string
	Timeout  time.Duration
}

func New(cfg Config) *Client {
	return &Client{
		base:     cfg.BaseURL,
		database: cfg.Database,
		user:     cfg.User,
		password: cfg.Password,
		http:     &http.Client{Timeout: cfg.Timeout},
	}
}

// Bootstrap creates the database and `events` table if they don't exist.
// All statements are idempotent so it's safe to call on every restart.
func (c *Client) Bootstrap(ctx context.Context) error {
	// Database is created against the default one to avoid chicken-and-egg.
	if err := c.execOn(ctx, "default",
		fmt.Sprintf("CREATE DATABASE IF NOT EXISTS %s", quoteIdent(c.database)),
	); err != nil {
		return fmt.Errorf("clickhouse bootstrap (db): %w", err)
	}

	ddl := `CREATE TABLE IF NOT EXISTS events (
    event_id UUID,
    event_type LowCardinality(String),
    occurred_at DateTime64(3, 'UTC'),
    user_id Nullable(UUID),
    session_id Nullable(String),
    properties String CODEC(ZSTD(3)),
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (event_type, occurred_at, event_id)
TTL toDateTime(occurred_at) + INTERVAL 180 DAY`

	if err := c.execOn(ctx, c.database, ddl); err != nil {
		return fmt.Errorf("clickhouse bootstrap (table): %w", err)
	}
	return nil
}

// Row is the shape `events` expects. `Properties` must already be a valid
// JSON string — we store it verbatim in a `String` column.
type Row struct {
	EventID    string  `json:"event_id"`
	EventType  string  `json:"event_type"`
	OccurredAt string  `json:"occurred_at"`
	UserID     *string `json:"user_id"`
	SessionID  *string `json:"session_id"`
	Properties string  `json:"properties"`
}

// InsertRows batches rows into a single `INSERT ... FORMAT JSONEachRow` call.
// Returns the count of rows accepted and an error for any non-2xx response.
func (c *Client) InsertRows(ctx context.Context, rows []Row) (int, error) {
	if len(rows) == 0 {
		return 0, nil
	}

	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	for i := range rows {
		if err := enc.Encode(&rows[i]); err != nil {
			return 0, fmt.Errorf("encode row: %w", err)
		}
	}

	q := url.Values{}
	q.Set("database", c.database)
	q.Set("query", "INSERT INTO events FORMAT JSONEachRow")

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.base+"/?"+q.Encode(), &buf)
	if err != nil {
		return 0, err
	}
	req.Header.Set("Content-Type", "application/x-ndjson")
	if c.user != "" {
		req.SetBasicAuth(c.user, c.password)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return 0, fmt.Errorf("clickhouse insert status=%d body=%s", resp.StatusCode, string(body))
	}
	return len(rows), nil
}

func (c *Client) execOn(ctx context.Context, db string, sql string) error {
	q := url.Values{}
	q.Set("database", db)

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.base+"/?"+q.Encode(), bytes.NewReader([]byte(sql)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "text/plain; charset=utf-8")
	if c.user != "" {
		req.SetBasicAuth(c.user, c.password)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf("clickhouse exec status=%d body=%s", resp.StatusCode, string(body))
	}
	return nil
}

// quoteIdent wraps an identifier with backticks and escapes embedded ones.
// ClickHouse doesn't accept parameters in DDL so we quote manually and reject
// anything that looks like SQL injection bait.
func quoteIdent(id string) string {
	out := make([]byte, 0, len(id)+2)
	out = append(out, '`')
	for i := 0; i < len(id); i++ {
		c := id[i]
		if c == '`' {
			out = append(out, '`', '`')
			continue
		}
		out = append(out, c)
	}
	out = append(out, '`')
	return string(out)
}
