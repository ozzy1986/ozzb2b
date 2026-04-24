/**
 * Server-side auth guards used by protected pages.
 *
 * Centralises the cookie + role checks so every gated route enforces the
 * same contract (and a future change to cookie names / roles only happens in
 * one place). Each guard performs the appropriate redirect server-side and
 * never returns when access is denied, so callers can use the result with
 * confidence.
 */

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { getMe } from './api';
import { authHeaders } from './server-fetch';
import { safeNextPath } from './safe-next';
import type { UserPublic } from './types';

const ACCESS_COOKIE = 'ozzb2b_at';

/**
 * Build a `?next=` query value safely from a path. Strips anything that could
 * be used for an open redirect (`//evil`, `https://evil`, ...).
 */
function buildNext(path: string): string {
  const safe = safeNextPath(path) ?? '/';
  return `next=${encodeURIComponent(safe)}`;
}

/**
 * Cheap presence check: redirects to /login if the access cookie is missing.
 * Use this when a page only needs to know "is the visitor logged in" and the
 * subsequent API calls will validate the session for real.
 */
export async function requireAuthCookie(currentPath: string): Promise<void> {
  const jar = await cookies();
  if (!jar.get(ACCESS_COOKIE)) {
    redirect(`/login?${buildNext(currentPath)}`);
  }
}

/**
 * Resolve and return the current user, redirecting to /login when the API
 * answers 401. Use this when downstream rendering depends on user fields
 * (role, email, etc.).
 */
export async function requireUser(currentPath: string): Promise<UserPublic> {
  await requireAuthCookie(currentPath);
  const headers = await authHeaders();
  const me = await getMe({ headers }).catch(() => null);
  if (!me) {
    redirect(`/login?${buildNext(currentPath)}`);
  }
  return me;
}

/**
 * Resolve and return the current user, ensuring it has the admin role.
 * Anyone else is redirected to the home page (admin URLs are not advertised
 * publicly, so a soft redirect is preferable to an explicit 403 page).
 */
export async function requireAdmin(currentPath: string): Promise<UserPublic> {
  const user = await requireUser(currentPath);
  if (user.role !== 'admin') {
    redirect('/');
  }
  return user;
}
