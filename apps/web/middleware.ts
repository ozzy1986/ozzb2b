import { NextResponse, type NextRequest } from 'next/server';

const CANONICAL_HOST = 'ozzb2b.com';

/**
 * One canonical origin for search engines: http:// and www. answer with a
 * 301 to https://ozzb2b.com. Apache in front preserves Host and sets
 * X-Forwarded-Proto; any other host (localhost, previews) is left alone.
 */
export function middleware(req: NextRequest) {
  const host = (req.headers.get('host') ?? '').toLowerCase().split(':')[0];
  const bare = host.replace(/^www\./, '');
  if (bare !== CANONICAL_HOST) return NextResponse.next();

  const proto = req.headers.get('x-forwarded-proto') ?? 'https';
  if (host === CANONICAL_HOST && proto === 'https') return NextResponse.next();

  const url = new URL(req.nextUrl.pathname + req.nextUrl.search, `https://${CANONICAL_HOST}`);
  return NextResponse.redirect(url, 301);
}

export const config = {
  // Skip Next internals and static assets; everything else gets normalised.
  matcher: ['/((?!_next/static|_next/image).*)'],
};
