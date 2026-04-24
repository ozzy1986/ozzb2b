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
//
// `expectedAudience` and `expectedIssuer` should mirror what the API mints
// (defaults `ozzb2b-ws-chat` / `ozzb2b`). When set, a token without the
// matching `aud`/`iss` is rejected. They may be left empty during the
// rolling deploy that introduces these claims, after which they should be
// configured for full defense-in-depth.
type Verifier struct {
	secret           []byte
	algorithm        string
	expectedAudience string
	expectedIssuer   string
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

// WithAudience returns a verifier that additionally enforces the JWT `aud`
// claim. Call this only when the API has been deployed with the matching
// `OZZB2B_JWT_AUDIENCE_WS_CHAT` value.
func (v *Verifier) WithAudience(audience string) *Verifier {
	cp := *v
	cp.expectedAudience = audience
	return &cp
}

// WithIssuer returns a verifier that additionally enforces the JWT `iss`
// claim.
func (v *Verifier) WithIssuer(issuer string) *Verifier {
	cp := *v
	cp.expectedIssuer = issuer
	return &cp
}

// Parse validates the signature + token type and returns normalised claims.
func (v *Verifier) Parse(raw string) (Claims, error) {
	if raw == "" {
		return Claims{}, errors.New("token is empty")
	}
	opts := []jwt.ParserOption{
		jwt.WithValidMethods([]string{v.algorithm}),
		jwt.WithIssuedAt(),
		jwt.WithLeeway(5 * time.Second),
	}
	if v.expectedAudience != "" {
		opts = append(opts, jwt.WithAudience(v.expectedAudience))
	}
	if v.expectedIssuer != "" {
		opts = append(opts, jwt.WithIssuer(v.expectedIssuer))
	}
	parser := jwt.NewParser(opts...)
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
