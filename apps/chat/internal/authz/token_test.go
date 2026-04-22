package authz

import (
	"strings"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

const testSecret = "this-is-a-32-byte-test-secret!!!"

func sign(t *testing.T, claims jwt.MapClaims) string {
	t.Helper()
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	s, err := tok.SignedString([]byte(testSecret))
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	return s
}

func baseClaims() jwt.MapClaims {
	return jwt.MapClaims{
		"sub": "00000000-0000-0000-0000-000000000001",
		"conv": "11111111-1111-1111-1111-111111111111",
		"typ": tokenTypeWsChat,
		"iat": time.Now().Add(-time.Second).Unix(),
		"exp": time.Now().Add(2 * time.Minute).Unix(),
		"jti": "j1",
	}
}

func TestVerifier_AcceptsValidToken(t *testing.T) {
	v, err := NewVerifier(testSecret, "HS256")
	if err != nil {
		t.Fatalf("new verifier: %v", err)
	}
	tok := sign(t, baseClaims())
	claims, err := v.Parse(tok)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if claims.UserID != "00000000-0000-0000-0000-000000000001" {
		t.Fatalf("unexpected sub: %s", claims.UserID)
	}
	if claims.ConversationID != "11111111-1111-1111-1111-111111111111" {
		t.Fatalf("unexpected conv: %s", claims.ConversationID)
	}
	if claims.ExpiresAt.Before(time.Now()) {
		t.Fatalf("expiration already past: %s", claims.ExpiresAt)
	}
}

func TestVerifier_RejectsExpiredToken(t *testing.T) {
	v, _ := NewVerifier(testSecret, "HS256")
	c := baseClaims()
	c["exp"] = time.Now().Add(-1 * time.Minute).Unix()
	if _, err := v.Parse(sign(t, c)); err == nil {
		t.Fatalf("expected error on expired token")
	}
}

func TestVerifier_RejectsWrongType(t *testing.T) {
	v, _ := NewVerifier(testSecret, "HS256")
	c := baseClaims()
	c["typ"] = "access"
	if _, err := v.Parse(sign(t, c)); err == nil {
		t.Fatalf("expected error on wrong type")
	}
}

func TestVerifier_RejectsWrongSecret(t *testing.T) {
	v, _ := NewVerifier(testSecret, "HS256")
	// Sign with a different secret.
	badTok := jwt.NewWithClaims(jwt.SigningMethodHS256, baseClaims())
	bad, err := badTok.SignedString([]byte("another-secret-not-matching-test"))
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	if _, err := v.Parse(bad); err == nil {
		t.Fatalf("expected error on wrong secret")
	}
}

func TestVerifier_RejectsEmpty(t *testing.T) {
	v, _ := NewVerifier(testSecret, "HS256")
	if _, err := v.Parse(""); err == nil {
		t.Fatalf("expected error on empty token")
	}
}

func TestNewVerifier_Validates(t *testing.T) {
	if _, err := NewVerifier("", "HS256"); err == nil {
		t.Fatalf("expected error for empty secret")
	}
	if _, err := NewVerifier("s", "none"); err == nil {
		t.Fatalf("expected error for unsupported algorithm")
	}
}

func TestVerifier_RejectsMissingSub(t *testing.T) {
	v, _ := NewVerifier(testSecret, "HS256")
	c := baseClaims()
	delete(c, "sub")
	_, err := v.Parse(sign(t, c))
	if err == nil {
		t.Fatalf("expected error on missing sub")
	}
	if !strings.Contains(err.Error(), "sub") {
		t.Fatalf("error should mention sub: %v", err)
	}
}
