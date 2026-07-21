import type { AnchorHTMLAttributes, ReactNode } from 'react';

type AppLinkHref =
  | string
  | {
      pathname?: string;
      search?: string;
      hash?: string;
      query?: Record<string, string | number | boolean | Array<string | number> | null | undefined>;
    };

type AppLinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
  href: AppLinkHref;
  children?: ReactNode;
};

/**
 * Stable internal navigation via a real anchor.
 *
 * Next.js 15 App Router soft navigation can preventDefault after a partial RSC
 * prefetch and then stall without committing the route (seen on the data-rich
 * home page). Native anchors always complete navigation.
 */
function hrefToString(href: AppLinkHref): string {
  if (typeof href === 'string') {
    return href;
  }

  const pathname = href.pathname ?? '';
  let search = '';
  if (typeof href.search === 'string' && href.search.length > 0) {
    search = href.search.startsWith('?') ? href.search : `?${href.search}`;
  } else if (href.query && typeof href.query === 'object') {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(href.query)) {
      if (value == null) continue;
      if (Array.isArray(value)) {
        for (const item of value) params.append(key, String(item));
      } else {
        params.set(key, String(value));
      }
    }
    const encoded = params.toString();
    if (encoded) search = `?${encoded}`;
  }

  const hash =
    typeof href.hash === 'string' && href.hash.length > 0
      ? href.hash.startsWith('#')
        ? href.hash
        : `#${href.hash}`
      : '';

  return `${pathname}${search}${hash}`;
}

export default function AppLink({ href, ...props }: AppLinkProps) {
  return <a {...props} href={hrefToString(href)} />;
}
