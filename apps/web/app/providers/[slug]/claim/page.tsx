import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { getProvider } from '@/lib/api';
import { ClaimFlow } from '@/components/ClaimFlow';
import { Breadcrumbs, type Crumb } from '@/components/Breadcrumbs';

export const metadata: Metadata = {
  title: 'Подтвердить владение',
  description: 'Подтвердите, что вы владелец карточки компании, через meta-тег на сайте.',
};

type RouteParams = Promise<{ slug: string }>;

export default async function ClaimPage({ params }: { params: RouteParams }) {
  const { slug } = await params;
  const jar = await cookies();
  const access = jar.get('ozzb2b_at');
  if (!access) {
    redirect(`/login?next=${encodeURIComponent(`/providers/${slug}/claim`)}`);
  }

  const provider = await getProvider(slug);
  if (!provider) {
    notFound();
  }

  const crumbs: Crumb[] = [
    { label: 'Главная', href: '/' },
    { label: 'Компании', href: '/providers?country=RU' },
    { label: provider.display_name, href: `/providers/${provider.slug}` },
    { label: 'Подтвердить владение' },
  ];

  if (provider.is_claimed) {
    return (
      <article>
        <Breadcrumbs items={crumbs} />
        <div className="sidebar-card">
          <h1>Эта компания уже подтверждена</h1>
          <p>
            Если вы считаете, что это ошибка, напишите нам на{' '}
            <a href="mailto:hello@ozzb2b.com">hello@ozzb2b.com</a>.
          </p>
          <Link className="chip" href={`/providers/${provider.slug}`}>
            ← Назад к карточке
          </Link>
        </div>
      </article>
    );
  }

  return (
    <article>
      <Breadcrumbs items={crumbs} />
      <ClaimFlow
        providerSlug={provider.slug}
        providerDisplayName={provider.display_name}
        providerWebsite={provider.website}
      />
    </article>
  );
}
