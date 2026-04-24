/**
 * Sanitises `?next=` redirect targets read from the URL.
 *
 * Returns the path only when it is a same-origin path (starts with a single
 * `/` and not `//` or `/\\`). For everything else returns `null` so callers
 * can fall back to a safe default. This blocks open-redirect attacks of the
 * form `?next=//evil.example` or `?next=https://evil.example`.
 */
export function safeNextPath(value: string | null | undefined): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  // Must start with a single '/' and not '//' (protocol-relative) nor '/\\'
  // (Windows-style backslash that some browsers normalise to '//').
  if (!trimmed.startsWith('/')) return null;
  if (trimmed.startsWith('//') || trimmed.startsWith('/\\')) return null;
  // Reject any control character; modern browsers tolerate them in URL bars
  // but they have no business in a same-origin redirect target.
  if (/[\x00-\x1F\x7F]/.test(trimmed)) return null;
  return trimmed;
}
