import Link from 'next/link';
import type { Metadata } from 'next';
import { listProviders, searchProviders } from '@/lib/api';
import type { ProviderListResponse, ProviderSummary, FacetValue } from '@/lib/types';
import { ProviderFilters } from '@/components/ProviderFilters';

export const revalidate = 30;

export const metadata: Metadata = {
  title: 'Providers',
  description: 'Browse and filter verified B2B outsourcing providers.',
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

  const listParams = {
    q,
    categories: toList(params.category),
    countries: toList(params.country),
    cities: toList(params.city),
    legal_forms: toList(params.legal_form),
    limit,
    offset,
    facets: true,
  };

  let data: ProviderListResponse | null = null;
  let engineLabel = 'catalog';
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

  const emptyFacet: FacetValue[] = [];

  return (
    <>
      <div className="hero">
        <h1>Providers</h1>
        <p>
          {q
            ? `Results for "${q}" — ${total} match${total === 1 ? '' : 'es'} (${engineLabel})`
            : `${total} providers`}
        </p>
        <form className="search-form" action="/providers" method="get">
          <input name="q" defaultValue={q ?? ''} placeholder="Search providers…" aria-label="Search" />
          <button type="submit">Search</button>
        </form>
      </div>

      <div className="layout">
        <aside>
          <ProviderFilters
            currentQ={q ?? ''}
            currentCategories={toList(params.category)}
            currentCountries={toList(params.country)}
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
              Showing {Math.min(total, items.length)} of {total}
            </span>
          </div>
          {items.length === 0 ? (
            <div className="empty">No providers match the current filters.</div>
          ) : (
            <div className="grid grid-providers">
              {items.map((p) => (
                <Link key={p.id} href={`/providers/${p.slug}`} className="card">
                  <h3>{p.display_name}</h3>
                  {p.description ? <p>{p.description}</p> : null}
                  <div className="meta">
                    {p.country ? <span className="chip">{p.country.name}</span> : null}
                    {p.city ? <span className="chip">{p.city.name}</span> : null}
                    {p.categories.slice(0, 3).map((c) => (
                      <span key={c.id} className="chip">
                        {c.name}
                      </span>
                    ))}
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
                  href={`/providers?${toQueryString({ ...params, offset: String(prevOffset) })}`}
                >
                  ← Previous
                </Link>
              ) : null}
              {nextOffset < total ? (
                <Link
                  className="chip"
                  href={`/providers?${toQueryString({ ...params, offset: String(nextOffset) })}`}
                >
                  Next →
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
