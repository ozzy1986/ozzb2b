#!/usr/bin/env bash
# Hard gate: rendered user-facing strings in apps/web must be Russian.
#
# Strategy: walk every JSX/TSX file under apps/web/{app,src/components} and
# inspect the visible text content of element bodies (`>TEXT</tag`). Any
# text that contains a 4+ letter English word (and no Cyrillic context) is
# rejected unless every English word is on the allowlist of approved
# technical tokens (brand names, JWT, API, etc.).
#
# We deliberately only flag text *between* opening and closing tags
# (`>...</tag`) to avoid TypeScript generics (`<T>`, `Promise<X>`) and
# attribute values, which both contain `>` and `<` for unrelated reasons.

set -euo pipefail

ROOT="${1:-apps/web}"

if [[ ! -d "$ROOT/app" || ! -d "$ROOT/src/components" ]]; then
    echo "::error::expected $ROOT/app and $ROOT/src/components"
    exit 1
fi

# Approved English technical tokens — lowercase entries only.
# Note: the suspect extractor greps [A-Za-z]{4,}, so every token here must be
# how the *alphabetic run* inside the source literal looks. For "ozzb2b" the
# alpha runs are "ozzb" and "b", so we list the real shapes ("ozzb" here).
ALLOWLIST=(
    "ozzb" "ozzb2b" "github" "ozzy" "ozzy1986"
    "json" "jwt" "uuid" "url" "http" "https" "ws" "wss"
    "api" "ssr" "rsc" "html" "css" "tsx" "jsx" "svg"
    "ios" "macos" "android" "chrome" "safari" "firefox"
    "google" "microsoft" "yandex" "tinkoff" "sber" "alfa"
    "telegram" "whatsapp" "meta"
    "next" "node" "vite" "vitest" "playwright"
    "false" "true" "null"
    "mailto" "hello" "robots" "sitemap"
)
allow_re=$(IFS='|'; echo "${ALLOWLIST[*]}")

failed=0
files=$(find "$ROOT/app" "$ROOT/src/components" -type f \( -name '*.tsx' -o -name '*.jsx' \) 2>/dev/null || true)

for file in $files; do
    # Pattern: `>` followed by text that contains a 4+ letter English word
    # and ends with `</` (start of a closing tag). This shape is unique to
    # JSX text content and almost never matches TypeScript generics or
    # attribute values, which is the false-positive class we worry about.
    while IFS= read -r line_no_text; do
        line_no=${line_no_text%%:*}
        text=${line_no_text#*:}

        # Extract the first `>...</` slice on the line.
        snippet=${text#*>}
        snippet=${snippet%%</*}
        snippet=$(printf '%s' "$snippet" | tr -d '\r' | sed -e 's/^[[:space:]]\{1,\}//' -e 's/[[:space:]]\{1,\}$//')
        [[ -z "$snippet" ]] && continue

        # Ignore JS expression-only text nodes like `{count}`.
        case "$snippet" in
            "{"*"}") continue ;;
        esac

        # Strip `{...}` JS expressions — their content is code identifiers,
        # not user-visible literals. Crude but good enough: inside JSX text
        # nodes there's no braces-in-strings ambiguity.
        snippet_stripped=$(printf '%s' "$snippet" | sed -e 's/{[^}]*}//g')
        # Strip email addresses (local@domain) — the local part is allowed
        # as plain text since the @ + TLD make intent unambiguous.
        snippet_stripped=$(printf '%s' "$snippet_stripped" | sed -E 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}//g')
        snippet=$(printf '%s' "$snippet_stripped" | tr -d '\r' | sed -e 's/^[[:space:]]\{1,\}//' -e 's/[[:space:]]\{1,\}$//')
        [[ -z "$snippet" ]] && continue

        suspect=$(printf '%s\n' "$snippet" \
            | grep -oE '[A-Za-z]{4,}' \
            | tr '[:upper:]' '[:lower:]' \
            | grep -Ev "^($allow_re)$" \
            || true)
        if [[ -n "$suspect" ]]; then
            # Bilingual UI text (e.g. "Войти через GitHub") is fine. We use
            # PCRE with the Cyrillic property so detection works even under
            # LC_ALL=C, where POSIX ranges like [А-Яа-яЁё] do not match UTF-8.
            if printf '%s' "$snippet" | grep -qP '\p{Cyrillic}'; then
                continue
            fi
            echo "::error file=$file,line=$line_no::user-facing English text: $snippet"
            failed=1
        fi
    done < <(grep -nE '>[^<>]*[A-Za-z]{4,}[^<>]*</[A-Za-z]' "$file" 2>/dev/null || true)
done

if [[ "$failed" -ne 0 ]]; then
    echo "::error::Russian-only UI policy violation. Translate the strings, or extend ALLOWLIST in scripts/check_web_ru_only.sh if the token is genuinely technical."
    exit 1
fi
echo "web-ru-only: clean"
