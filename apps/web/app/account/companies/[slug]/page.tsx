import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getProvider, listMyProviders } from '@/lib/api';
import { authHeaders } from '@/lib/server-fetch';
import { requireAuthCookie } from '@/lib/auth-guard';
import { Breadcrumbs, type Crumb } from '@/components/Breadcrumbs';
import { OwnedProviderEditor } from '@/components/OwnedProviderEditor';

export const metadata: Metadata = {
  title: 'Редактирование компании',
  robots: { index: false, follow: false },
};

export const revalidate = 0;
export const dynamic = 'force-dynamic';

type RouteParams = Promise<{ slug: string }>;

export default async function OwnedProviderEditPage({ params }: { params: RouteParams }) {
  const { slug } = await params;
  await requireAuthCookie(`/account/companies/${slug}`);

  const headers = await authHeaders();
  const [mine, provider] = await Promise.all([
    listMyProviders({ headers }).catch(() => []),
    getProvider(slug),
  ]);

  if (!provider) notFound();
  const isMine = mine.some((p) => p.slug === slug);
  if (!isMine) {
    return (
      <article>
        <Breadcrumbs
          items={[
            { label: 'Главная', href: '/' },
            { label: 'Мои компании', href: '/account/companies' },
            { label: provider.display_name },
          ]}
        />
        <div className="sidebar-card">
          <h1>Нет доступа</h1>
          <p>
            Эта компания принадлежит другому владельцу. Если это ошибка — напишите на{' '}
            <a href="mailto:hello@ozzb2b.com">hello@ozzb2b.com</a>.
          </p>
          <Link className="chip" href="/account/companies">
            ← К моим компаниям
          </Link>
        </div>
      </article>
    );
  }

  const crumbs: Crumb[] = [
    { label: 'Главная', href: '/' },
    { label: 'Мои компании', href: '/account/companies' },
    { label: provider.display_name },
  ];

  return (
    <article>
      <Breadcrumbs items={crumbs} />
      <div className="hero">
        <h1>Редактирование: {provider.display_name}</h1>
        <p>
          Изменения сразу попадают в публичную карточку{' '}
          <Link href={`/providers/${provider.slug}`}>{provider.slug}</Link>.
        </p>
      </div>
      <OwnedProviderEditor initial={provider} />
    </article>
  );
}
