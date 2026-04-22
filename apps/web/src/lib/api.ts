import type {
  Category,
  CategoryTreeNode,
  City,
  Country,
  LegalForm,
  ProviderDetail,
  ProviderListResponse,
} from './types';

const API_URL =
  process.env.OZZB2B_API_URL ?? process.env.NEXT_PUBLIC_OZZB2B_API_URL ?? 'http://localhost:8001';

export type ApiHealth = { ok: true; version: string } | { ok: false; error: string };

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    cache: 'no-store',
    next: { revalidate: 0 },
    headers: {
      accept: 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new Error(`${path} failed with ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function getApiHealth(): Promise<ApiHealth> {
  try {
    const body = await fetchJson<{ status: string; version: string }>('/health');
    if (body.status !== 'ok') return { ok: false, error: body.status };
    return { ok: true, version: body.version };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'unknown error' };
  }
}

export async function getCategories(): Promise<Category[]> {
  return fetchJson<Category[]>('/categories');
}

export async function getCategoryTree(): Promise<CategoryTreeNode[]> {
  return fetchJson<CategoryTreeNode[]>('/categories/tree');
}

export async function getCountries(): Promise<Country[]> {
  return fetchJson<Country[]>('/countries');
}

export async function getCities(country?: string): Promise<City[]> {
  const qs = country ? `?country=${encodeURIComponent(country)}` : '';
  return fetchJson<City[]>(`/cities${qs}`);
}

export async function getLegalForms(country?: string): Promise<LegalForm[]> {
  const qs = country ? `?country=${encodeURIComponent(country)}` : '';
  return fetchJson<LegalForm[]>(`/legal-forms${qs}`);
}

export type ProviderListParams = {
  q?: string;
  categories?: string[];
  countries?: string[];
  cities?: string[];
  legal_forms?: string[];
  limit?: number;
  offset?: number;
  facets?: boolean;
};

function buildQuery(params: ProviderListParams): string {
  const sp = new URLSearchParams();
  if (params.q) sp.set('q', params.q);
  for (const v of params.categories ?? []) sp.append('category', v);
  for (const v of params.countries ?? []) sp.append('country', v);
  for (const v of params.cities ?? []) sp.append('city', v);
  for (const v of params.legal_forms ?? []) sp.append('legal_form', v);
  if (params.limit != null) sp.set('limit', String(params.limit));
  if (params.offset != null) sp.set('offset', String(params.offset));
  if (params.facets) sp.set('facets', 'true');
  const qs = sp.toString();
  return qs ? `?${qs}` : '';
}

export async function listProviders(params: ProviderListParams = {}): Promise<ProviderListResponse> {
  return fetchJson<ProviderListResponse>(`/providers${buildQuery(params)}`);
}

export async function getProvider(slug: string): Promise<ProviderDetail | null> {
  try {
    return await fetchJson<ProviderDetail>(`/providers/${encodeURIComponent(slug)}`);
  } catch {
    return null;
  }
}

export async function searchProviders(params: ProviderListParams & { q: string }) {
  const qs = buildQuery(params);
  return fetchJson<{
    total: number;
    limit: number;
    offset: number;
    engine: string;
    items: import('./types').ProviderSummary[];
  }>(`/search${qs}`);
}
