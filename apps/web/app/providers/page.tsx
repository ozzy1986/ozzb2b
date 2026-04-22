import Link from 'next/link';
import type { Metadata } from 'next';
import { listProviders, searchProviders } from '@/lib/api';
import type { ProviderListResponse, ProviderSummary, FacetValue } from '@/lib/types';
import { ProviderFilters } from '@/components/ProviderFilters';
import { trCategory, trCity, trCountry } from '@/lib/ru';
import { Breadcrumbs, type Crumb } from '@/components/Breadcrumbs';
import { FreshnessBadge } from '@/components/FreshnessBadge';

export const revalidate = 30;

export const metadata: Metadata = {
  title: 'Компании',
  description: 'Каталог проверенных B2B-компаний в России с фильтрами и поиском.',
};

type SearchParams = {
  q?: string | string[];
  category?: string | string[];
  country?: string | string[];
  city?: string | string[];
  legal_form?: string | string[];
  offset?: string;
};

function toList(v: string | string[] | undefined): string[] {
  if (v == null) return [];
  return Array.isArray(v) ? v : [v];
}

export default async function ProvidersPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const q = typeof params.q === 'string' ? params.q : undefined;
  const offset = Math.max(0, Number.parseInt(params.offset ?? '0', 10) || 0);
  const limit = 24;
  const rawCountries = toList(params.country);
  const effectiveCountries = rawCountries.length > 0 ? rawCountries : ['RU'];

  const listParams = {
    q,
    categories: toList(params.category),
    countries: effectiveCountries,
    cities: toList(params.city),
    legal_forms: toList(params.legal_form),
    limit,
    offset,
    facets: true,
  };

  let data: ProviderListResponse | null = null;
  let engineLabel = 'каталог';
  if (q) {
    try {
      const search = await searchProviders({ ...listParams, q });
      data = {
        total: search.total,
        limit: search.limit,
        offset: search.offset,
        items: search.items,
        facets: null,
      };
      engineLabel = search.engine;
    } catch {
      data = await listProviders(listParams);
    }
  } else {
    data = await listProviders(listParams);
  }

  const items: ProviderSummary[] = data?.items ?? [];
  const facets = data?.facets ?? null;
  const total = data?.total ?? 0;
  const nextOffset = offset + limit;
  const prevOffset = Math.max(0, offset - limit);
  const linkParams: SearchParams = {
    ...params,
    country: effectiveCountries,
  };

  const emptyFacet: FacetValue[] = [];

  const activeFilters =
    toList(params.category).length +
    toList(params.city).length +
    toList(params.legal_form).length +
    (q ? 1 : 0);

  const crumbs: Crumb[] = [
    { label: 'Главная', href: '/' },
    { label: 'Компании' },
  ];

  return (
    <>
      <Breadcrumbs items={crumbs} />
      <div className="hero">
        <h1>Компании</h1>
        <p>
          {q
            ? `Результаты по запросу "${q}" — ${total} (${engineLabel})`
            : `${total} компаний`}
        </p>
        <form className="search-form" action="/providers" method="get">
          <input type="hidden" name="country" value="RU" />
          <input name="q" defaultValue={q ?? ''} placeholder="Поиск компаний..." aria-label="Поиск" />
          <button type="submit">Искать</button>
        </form>
      </div>

      <div className="layout">
        <aside>
          <div className="filters-head">
            <strong>Фильтры</strong>
            {activeFilters > 0 ? (
              <Link className="filter-clear" href="/providers?country=RU">
                Сбросить ({activeFilters})
              </Link>
            ) : null}
          </div>
          <ProviderFilters
            currentQ={q ?? ''}
            currentCategories={toList(params.category)}
            currentCountries={effectiveCountries}
            currentCities={toList(params.city)}
            currentLegalForms={toList(params.legal_form)}
            categories={facets?.categories ?? emptyFacet}
            countries={facets?.countries ?? emptyFacet}
            cities={facets?.cities ?? emptyFacet}
            legalForms={facets?.legal_forms ?? emptyFacet}
          />
        </aside>
        <section>
          <div className="listing-head">
            <span className="total">
              Показано {Math.min(total, items.length)} из {total}
            </span>
          </div>
          {items.length === 0 ? (
            <div className="empty">По текущим фильтрам ничего не найдено.</div>
          ) : (
            <div className="grid grid-providers">
              {items.map((p) => (
                <Link key={p.id} href={`/providers/${p.slug}`} className="card">
                  <h3>{p.display_name}</h3>
                  {p.description ? <p>{p.description}</p> : null}
                  <div className="meta">
                    {p.country ? (
                      <span className="chip">{trCountry(p.country.code, p.country.name)}</span>
                    ) : null}
                    {p.city ? <span className="chip">{trCity(p.city.name)}</span> : null}
                    {p.categories.slice(0, 3).map((c) => (
                      <span key={c.id} className="chip">
                        {trCategory(c.slug, c.name)}
                      </span>
                    ))}
                    <FreshnessBadge lastScrapedAt={p.last_scraped_at} />
                  </div>
                </Link>
              ))}
            </div>
          )}

          {total > limit ? (
            <nav aria-label="Pagination" style={{ display: 'flex', gap: 12, marginTop: 24 }}>
              {offset > 0 ? (
                <Link
                  className="chip"
                  href={`/providers?${toQueryString({ ...linkParams, offset: String(prevOffset) })}`}
                >
                  ← Назад
                </Link>
              ) : null}
              {nextOffset < total ? (
                <Link
                  className="chip"
                  href={`/providers?${toQueryString({ ...linkParams, offset: String(nextOffset) })}`}
                >
                  Далее →
                </Link>
              ) : null}
            </nav>
          ) : null}
        </section>
      </div>
    </>
  );
}

function toQueryString(params: Record<string, string | string[] | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v == null) continue;
    if (Array.isArray(v)) {
      for (const item of v) sp.append(k, item);
    } else {
      sp.set(k, v);
    }
  }
  return sp.toString();
}
