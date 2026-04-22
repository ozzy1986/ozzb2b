package config

import (
	"os"
	"testing"
)

// AllowedOrigins patterns are matched by coder/websocket against the host of
// the browser's Origin header (scheme stripped). Keeping this as a test so a
// future refactor cannot silently re-introduce scheme-prefixed defaults and
// break live WS connections from the public site.
func TestDefaultAllowedOriginsAreBareHostnames(t *testing.T) {
	t.Setenv("OZZB2B_JWT_SECRET", "x")
	t.Setenv("OZZB2B_CHAT_ALLOWED_ORIGINS", "")

	cfg, err := Load("test")
	if err != nil {
		t.Fatalf("Load: %v", err)
	}

	seen := map[string]bool{}
	for _, o := range cfg.AllowedOrigins {
		seen[o] = true
		if containsScheme(o) {
			t.Fatalf("allowed origin %q must not contain a scheme", o)
		}
	}
	for _, required := range []string{"ozzb2b.com", "www.ozzb2b.com"} {
		if !seen[required] {
			t.Fatalf("default allowed origins must include %q, got %v", required, cfg.AllowedOrigins)
		}
	}
}

func TestAllowedOriginsOverride(t *testing.T) {
	t.Setenv("OZZB2B_JWT_SECRET", "x")
	t.Setenv("OZZB2B_CHAT_ALLOWED_ORIGINS", "example.com, other.example.com ")

	cfg, err := Load("test")
	if err != nil {
		t.Fatalf("Load: %v", err)
	}

	if len(cfg.AllowedOrigins) != 2 ||
		cfg.AllowedOrigins[0] != "example.com" ||
		cfg.AllowedOrigins[1] != "other.example.com" {
		t.Fatalf("unexpected origins: %v", cfg.AllowedOrigins)
	}
}

func TestLoadRequiresJWTSecret(t *testing.T) {
	_ = os.Unsetenv("OZZB2B_JWT_SECRET")
	if _, err := Load("test"); err == nil {
		t.Fatalf("expected error when JWT secret is missing")
	}
}

func containsScheme(s string) bool {
	for i := 0; i+2 < len(s); i++ {
		if s[i] == ':' && s[i+1] == '/' && s[i+2] == '/' {
			return true
		}
	}
	return false
}
