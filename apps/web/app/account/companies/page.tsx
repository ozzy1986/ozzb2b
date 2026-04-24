import type { Metadata } from 'next';
import Link from 'next/link';
import { listMyProviders, listMyClaims } from '@/lib/api';
import { authHeaders } from '@/lib/server-fetch';
import { requireAuthCookie } from '@/lib/auth-guard';
import { Breadcrumbs, type Crumb } from '@/components/Breadcrumbs';

export const metadata: Metadata = {
  title: 'Мои компании',
  robots: { index: false, follow: false },
};

export const revalidate = 0;
export const dynamic = 'force-dynamic';

export default async function MyCompaniesPage() {
  await requireAuthCookie('/account/companies');

  const headers = await authHeaders();
  const [providersResult, claimsResult] = await Promise.allSettled([
    listMyProviders({ headers }),
    listMyClaims({ headers }),
  ]);
  const providers = providersResult.status === 'fulfilled' ? providersResult.value : [];
  const claims = claimsResult.status === 'fulfilled' ? claimsResult.value : [];

  const pendingClaims = claims.filter((c) => c.status === 'pending');
  const rejectedClaims = claims.filter((c) => c.status === 'rejected');

  const crumbs: Crumb[] = [
    { label: 'Главная', href: '/' },
    { label: 'Мои компании' },
  ];

  return (
    <article>
      <Breadcrumbs items={crumbs} />
      <div className="hero">
        <h1>Мои компании</h1>
        <p>
          Здесь собраны компании, владение которыми вы подтвердили, и заявки на подтверждение,
          которые вы открыли.
        </p>
      </div>

      <section className="sidebar-card">
        <h2 style={{ marginTop: 0 }}>Подтверждённые компании</h2>
        {providers.length === 0 ? (
          <p>
            Пока нет подтверждённых компаний. Найдите свою карточку в{' '}
            <Link href="/providers?country=RU">каталоге</Link> и нажмите «Это моя компания».
          </p>
        ) : (
          <div className="grid grid-providers">
            {providers.map((p) => (
              <Link key={p.id} href={`/account/companies/${p.slug}`} className="card">
                <h3>{p.display_name}</h3>
                {p.description ? <p>{p.description.slice(0, 140)}</p> : null}
                <div className="meta">
                  {p.city ? <span className="chip">{p.city.name}</span> : null}
                  {p.is_claimed ? <span className="chip">Подтверждена</span> : null}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {pendingClaims.length > 0 ? (
        <section className="sidebar-card" style={{ marginTop: 16 }}>
          <h2 style={{ marginTop: 0 }}>Ожидают подтверждения</h2>
          <ul>
            {pendingClaims.map((c) => (
              <li key={c.id}>
                Заявка от {new Date(c.created_at).toLocaleDateString('ru-RU')} —
                <span className="chip" style={{ marginLeft: 8 }}>{c.method}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {rejectedClaims.length > 0 ? (
        <section className="sidebar-card" style={{ marginTop: 16 }}>
          <h2 style={{ marginTop: 0 }}>Отклонённые заявки</h2>
          <ul>
            {rejectedClaims.map((c) => (
              <li key={c.id}>
                {new Date(c.rejected_at ?? c.updated_at).toLocaleDateString('ru-RU')} —{' '}
                {c.rejected_reason ?? 'без указания причины'}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </article>
  );
}
