/**
 * Server-side helpers that forward the incoming request's cookies to the API
 * so authenticated SSR pages behave the same way as their CSR counterparts.
 *
 * Next.js does not automatically propagate cookies from `fetch` calls made
 * during render; we have to read them from `next/headers` and set them
 * explicitly on the outbound request.
 */
import { cookies } from 'next/headers';

export async function authHeaders(): Promise<Record<string, string>> {
  const store = await cookies();
  const cookieString = store
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join('; ');
  return cookieString ? { cookie: cookieString } : {};
}
