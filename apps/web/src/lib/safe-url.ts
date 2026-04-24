/**
 * Returns a safe URL string suitable for `<a href>` from arbitrary input.
 *
 * Only `http:`, `https:`, `mailto:` and `tel:` schemes are allowed. Anything
 * else (`javascript:`, `data:`, `vbscript:`, ...) is rejected and the
 * function returns `null`, so callers can render the field as plain text or
 * skip the link entirely.
 *
 * Inputs without an explicit scheme are treated as `https://` candidates so
 * a stored value like `example.com` becomes `https://example.com`.
 */

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:', 'mailto:', 'tel:']);

export function safeUrl(value: string | null | undefined): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;

  let candidate = trimmed;
  // Heuristic: a value without `://`, `mailto:` or `tel:` is treated as a
  // bare host/path and gets `https://` prepended so we still get a usable
  // link without trusting whatever scheme the database happens to hold.
  if (!/^[a-z][a-z0-9+\-.]*:/i.test(candidate)) {
    candidate = `https://${candidate}`;
  }

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    return null;
  }
  if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) return null;
  return parsed.toString();
}
