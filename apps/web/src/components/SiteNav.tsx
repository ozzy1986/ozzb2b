'use client';

import Link from 'next/link';
import { useCurrentUser } from './useCurrentUser';

/**
 * Top navigation. Public links are always visible; admin-only entries are
 * rendered client-side once we know who the current user is.
 */
export function SiteNav() {
  const current = useCurrentUser();

  return (
    <nav className="site-nav" aria-label="Основная навигация">
      <Link href="/providers">Компании</Link>
      <Link href="/categories">Категории</Link>
      <Link href="/chat">Чаты</Link>
      {current.status === 'authenticated' &&
      (current.user.role === 'provider_owner' || current.user.role === 'admin') ? (
        <Link href="/account/companies">Мои компании</Link>
      ) : null}
      {current.status === 'authenticated' && current.user.role === 'admin' ? (
        <Link href="/admin/analytics">Аналитика</Link>
      ) : null}
      <a href="https://github.com/ozzy1986/ozzb2b" target="_blank" rel="noreferrer">
        GitHub
      </a>
    </nav>
  );
}
