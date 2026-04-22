// Package metrics registers the events consumer's Prometheus counters.
// All counters live in the default registry so a single `promhttp.Handler()`
// exposes them alongside the runtime's default process/go metrics.
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	BatchesInserted = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_events_batches_inserted_total",
			Help: "Number of batches successfully inserted into ClickHouse.",
		},
	)

	RowsInserted = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_events_rows_inserted_total",
			Help: "Number of rows written to ClickHouse.",
		},
	)

	InsertErrors = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_events_insert_errors_total",
			Help: "Failed attempts to insert a batch into ClickHouse.",
		},
	)

	ReadErrors = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_events_read_errors_total",
			Help: "Failed attempts to read from the Redis stream.",
		},
	)

	AckErrors = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_events_ack_errors_total",
			Help: "Failed attempts to ACK messages on the Redis stream.",
		},
	)

	MalformedDropped = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_events_malformed_dropped_total",
			Help: "Stream entries dropped because the envelope couldn't be parsed.",
		},
	)
)
