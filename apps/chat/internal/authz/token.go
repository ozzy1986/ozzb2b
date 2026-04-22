// Package authz validates short-lived chat WebSocket tokens issued by the API.
//
// The signing secret must be shared with the API (same OZZB2B_JWT_SECRET).
// We intentionally verify both the signature and the token type so that a
// long-lived access token cannot be replayed on the WS gateway.
package authz

import (
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

const tokenTypeWsChat = "ws_chat"

// Claims is the minimum set of fields we require from a chat token.
type Claims struct {
	UserID         string
	ConversationID string
	ExpiresAt      time.Time
}

// Verifier decodes and validates chat tokens against a configured HMAC secret.
type Verifier struct {
	secret    []byte
	algorithm string
}

// NewVerifier builds a Verifier from the shared HMAC secret and algorithm.
// We only accept HS256/HS384/HS512 — anything else is rejected up front so a
// misconfiguration cannot degrade to a weaker algorithm.
func NewVerifier(secret, algorithm string) (*Verifier, error) {
	if secret == "" {
		return nil, errors.New("jwt secret must not be empty")
	}
	switch algorithm {
	case "HS256", "HS384", "HS512":
	default:
		return nil, fmt.Errorf("unsupported jwt algorithm %q", algorithm)
	}
	return &Verifier{secret: []byte(secret), algorithm: algorithm}, nil
}

// Parse validates the signature + token type and returns normalised claims.
func (v *Verifier) Parse(raw string) (Claims, error) {
	if raw == "" {
		return Claims{}, errors.New("token is empty")
	}
	parser := jwt.NewParser(
		jwt.WithValidMethods([]string{v.algorithm}),
		jwt.WithIssuedAt(),
		jwt.WithLeeway(5*time.Second),
	)
	parsed, err := parser.Parse(raw, func(t *jwt.Token) (any, error) {
		return v.secret, nil
	})
	if err != nil {
		return Claims{}, fmt.Errorf("parse token: %w", err)
	}
	if !parsed.Valid {
		return Claims{}, errors.New("token is not valid")
	}
	mc, ok := parsed.Claims.(jwt.MapClaims)
	if !ok {
		return Claims{}, errors.New("unexpected claims type")
	}
	if typ, _ := mc["typ"].(string); typ != tokenTypeWsChat {
		return Claims{}, fmt.Errorf("unexpected token type %q", typ)
	}
	sub, _ := mc["sub"].(string)
	conv, _ := mc["conv"].(string)
	if sub == "" || conv == "" {
		return Claims{}, errors.New("token missing sub or conv claim")
	}
	expUnix, err := mc.GetExpirationTime()
	if err != nil || expUnix == nil {
		return Claims{}, errors.New("token missing exp claim")
	}
	return Claims{
		UserID:         sub,
		ConversationID: conv,
		ExpiresAt:      expUnix.Time,
	}, nil
}
