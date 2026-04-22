// Package metrics registers the chat gateway's Prometheus counters.
//
// All counters live in the default Prometheus registry so that a single
// `promhttp.Handler()` on the main mux can expose them without extra wiring.
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	WSConnections = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "ozzb2b_chat_ws_connections_total",
			Help: "WebSocket connection outcomes.",
		},
		[]string{"outcome"},
	)

	WSMessagesForwarded = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_chat_ws_messages_forwarded_total",
			Help: "Messages forwarded from Redis to a connected client.",
		},
	)

	RedisSubscribeErrors = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ozzb2b_chat_redis_subscribe_errors_total",
			Help: "Failed attempts to subscribe to a conversation channel.",
		},
	)
)
