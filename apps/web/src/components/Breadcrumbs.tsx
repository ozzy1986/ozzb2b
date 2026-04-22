import Link from 'next/link';
import type { ReactElement } from 'react';

export type Crumb = {
  label: string;
  href?: string;
};

/**
 * Renders a visual breadcrumb trail and the matching schema.org
 * `BreadcrumbList` JSON-LD so search engines see the hierarchy.
 *
 * The final crumb is intentionally not rendered as a link (it's the
 * current page), and its `aria-current="page"` is set for screen readers.
 */
export function Breadcrumbs({
  items,
  baseUrl = 'https://ozzb2b.com',
}: {
  items: Crumb[];
  baseUrl?: string;
}): ReactElement | null {
  if (items.length === 0) return null;

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.label,
      item: c.href ? (c.href.startsWith('http') ? c.href : `${baseUrl}${c.href}`) : undefined,
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <nav className="breadcrumbs" aria-label="Хлебные крошки">
        {items.map((c, i) => {
          const isLast = i === items.length - 1;
          return (
            <span key={`${i}-${c.label}`}>
              {c.href && !isLast ? <Link href={c.href}>{c.label}</Link> : (
                <span aria-current={isLast ? 'page' : undefined}>{c.label}</span>
              )}
              {!isLast ? <span className="sep"> / </span> : null}
            </span>
          );
        })}
      </nav>
    </>
  );
}
