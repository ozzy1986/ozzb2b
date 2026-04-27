import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getProvider } from '@/lib/api';
import type { ProviderDetail } from '@/lib/types';
import { trCategory, trCity, trCountry, trLegalForm } from '@/lib/ru';
import { safeUrl } from '@/lib/safe-url';
import { ContactProviderButton } from '@/components/ContactProviderButton';
import { Breadcrumbs, type Crumb } from '@/components/Breadcrumbs';
import { FreshnessBadge } from '@/components/FreshnessBadge';
import { ClaimProviderButton } from '@/components/ClaimProviderButton';
import { primaryCategories, subcategories } from '@/lib/categories';

export const revalidate = 60;

type RouteParams = Promise<{ slug: string }>;

export async function generateMetadata({ params }: { params: RouteParams }): Promise<Metadata> {
  const { slug } = await params;
  const p = await getProvider(slug);
  if (!p) return { title: 'Компания не найдена' };
  return {
    title: p.display_name,
    description: p.description?.slice(0, 180) ?? `B2B-компания — ${p.display_name}`,
    alternates: { canonical: `/providers/${p.slug}` },
    openGraph: {
      title: p.display_name,
      description: p.description?.slice(0, 180) ?? undefined,
      url: `/providers/${p.slug}`,
      type: 'profile',
    },
  };
}

function buildJsonLd(p: ProviderDetail) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: p.display_name,
    legalName: p.legal_name,
    description: p.description ?? undefined,
    url: p.website ?? `https://ozzb2b.com/providers/${p.slug}`,
    email: p.email ?? undefined,
    telephone: p.phone ?? undefined,
    foundingDate: p.year_founded ? String(p.year_founded) : undefined,
    address: p.address
      ? {
          '@type': 'PostalAddress',
          streetAddress: p.address,
          addressLocality: p.city?.name,
          addressCountry: p.country?.code,
        }
      : undefined,
    sameAs: p.website ? [p.website] : undefined,
    knowsAbout: p.categories.map((c) => c.name),
  };
}

export default async function ProviderDetailPage({ params }: { params: RouteParams }) {
  const { slug } = await params;
  const p = await getProvider(slug);
  if (!p) {
    notFound();
  }
  const jsonLd = buildJsonLd(p);
  const mainCategories = primaryCategories(p.categories);
  const specialties = subcategories(p.categories);
  const breadcrumbCategory = mainCategories[0] ?? p.categories[0];
  const crumbs: Crumb[] = [
    { label: 'Главная', href: '/' },
    { label: 'Компании', href: '/providers?country=RU' },
    ...(breadcrumbCategory
      ? [
          {
            label: trCategory(breadcrumbCategory.slug, breadcrumbCategory.name),
            href: `/providers?country=RU&category=${breadcrumbCategory.slug}`,
          },
        ]
      : []),
    { label: p.display_name },
  ];

  return (
    <article>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Breadcrumbs items={crumbs} />
      <div className="detail-header">
        <div>
          <h1>{p.display_name}</h1>
          <div className="chips">
            {p.country ? (
              <span className="chip">{trCountry(p.country.code, p.country.name)}</span>
            ) : null}
            {p.city ? <span className="chip">{trCity(p.city.name)}</span> : null}
            {p.legal_form ? (
              <span className="chip">{trLegalForm(p.legal_form.code, p.legal_form.name)}</span>
            ) : null}
            {p.year_founded ? <span className="chip">Основана в {p.year_founded}</span> : null}
            {p.employee_count_range ? <span className="chip">{p.employee_count_range} сотрудников</span> : null}
            <FreshnessBadge lastScrapedAt={p.last_scraped_at} />
          </div>
        </div>
        <div>
          <Link href="/providers?country=RU" className="chip">
            ← К списку компаний
          </Link>
        </div>
      </div>

      <div className="detail-grid">
        <div className="prose">
          <section>
            <h2>О компании</h2>
            <p>{p.description ?? 'Описание пока не добавлено.'}</p>
          </section>
          <section>
            <h2>Основные направления</h2>
            <div className="chips">
              {mainCategories.map((c) => (
                <Link key={c.id} href={`/providers?country=RU&category=${c.slug}`} className="chip">
                  {trCategory(c.slug, c.name)}
                </Link>
              ))}
            </div>
            {specialties.length > 0 ? (
              <>
                <h3>Специализации</h3>
                <div className="chips">
                  {specialties.map((c) => (
                    <Link key={c.id} href={`/providers?country=RU&category=${c.slug}`} className="chip">
                      {trCategory(c.slug, c.name)}
                    </Link>
                  ))}
                </div>
              </>
            ) : null}
          </section>
        </div>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="sidebar-card">
            <h3>Связаться с компанией</h3>
            <p className="auth-hint" style={{ marginTop: 0 }}>
              Откройте прямой чат с представителем — без раскрытия ваших контактов.
            </p>
            <ContactProviderButton providerSlug={p.slug} />
          </div>

          <ClaimProviderButton providerSlug={p.slug} isClaimed={p.is_claimed} />

          <div className="sidebar-card">
            <h3>Контакты</h3>
            <dl>
              {(() => {
                const safeWebsite = safeUrl(p.website);
                return safeWebsite ? (
                  <>
                    <dt>Сайт</dt>
                    <dd>
                      <a href={safeWebsite} target="_blank" rel="noreferrer">
                        {safeWebsite.replace(/^https?:\/\//, '')}
                      </a>
                    </dd>
                  </>
                ) : null;
              })()}
              {(() => {
                const safeEmail = p.email ? safeUrl(`mailto:${p.email}`) : null;
                return safeEmail && p.email ? (
                  <>
                    <dt>Электронная почта</dt>
                    <dd>
                      <a href={safeEmail}>{p.email}</a>
                    </dd>
                  </>
                ) : null;
              })()}
              {(() => {
                const safePhone = p.phone
                  ? safeUrl(`tel:${p.phone.replace(/\s+/g, '')}`)
                  : null;
                return safePhone && p.phone ? (
                  <>
                    <dt>Телефон</dt>
                    <dd>
                      <a href={safePhone}>{p.phone}</a>
                    </dd>
                  </>
                ) : null;
              })()}
              {p.address ? (
                <>
                  <dt>Адрес</dt>
                  <dd>{p.address}</dd>
                </>
              ) : null}
            </dl>
          </div>

          <div className="sidebar-card">
            <h3>Данные компании</h3>
            <dl>
              <dt>Юридическое наименование</dt>
              <dd>{p.legal_name}</dd>
              {p.registration_number ? (
                <>
                  <dt>Рег. номер</dt>
                  <dd>{p.registration_number}</dd>
                </>
              ) : null}
              {p.tax_id ? (
                <>
                  <dt>ИНН / налоговый ID</dt>
                  <dd>{p.tax_id}</dd>
                </>
              ) : null}
              {p.source ? (
                <>
                  <dt>Источник</dt>
                  <dd>{p.source}</dd>
                </>
              ) : null}
            </dl>
          </div>
        </aside>
      </div>
    </article>
  );
}
