import type {
  AnalyticsSummary,
  Category,
  CategoryTreeNode,
  ChatMessage,
  City,
  Conversation,
  Country,
  LegalForm,
  ProviderDetail,
  ProviderListResponse,
  TokenResponse,
  TopProviders,
  TopQueries,
  UserPublic,
  WsTokenResponse,
} from './types';

const SERVER_API_URL = process.env.OZZB2B_API_URL ?? 'http://localhost:8001';
// IMPORTANT: `NEXT_PUBLIC_*` values are injected at build time. If absent,
// falling back to localhost breaks the production browser client (it will call
// the visitor's own localhost). Use the public API domain as a safe fallback.
const PUBLIC_API_URL =
  process.env.NEXT_PUBLIC_OZZB2B_API_URL ?? 'https://api.ozzb2b.com';

function apiUrl(): string {
  return typeof window === 'undefined' ? SERVER_API_URL : PUBLIC_API_URL;
}

export type ApiHealth = { ok: true; version: string } | { ok: false; error: string };

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

function toApiDetail(raw: unknown, fallback: string): string {
  if (typeof raw === 'string' && raw.trim()) return raw;
  if (Array.isArray(raw)) {
    const parts = raw
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const obj = item as { loc?: unknown; msg?: unknown };
          const msg = typeof obj.msg === 'string' ? obj.msg : null;
          if (!msg) return null;
          if (Array.isArray(obj.loc)) {
            const field = obj.loc
              .map((v) => (typeof v === 'string' ? v : null))
              .filter(Boolean)
              .join('.');
            if (field) return `${field}: ${msg}`;
          }
          return msg;
        }
        return null;
      })
      .filter((v): v is string => Boolean(v));
    if (parts.length > 0) return parts.join('; ');
  }
  return fallback;
}

function buildHeaders(init?: RequestInit): HeadersInit {
  return {
    accept: 'application/json',
    ...(init?.headers ?? {}),
  };
}

async function executeFetch<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${apiUrl()}${path}`, init);
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      detail = toApiDetail(body?.detail, detail);
    } catch {
      // keep status-only detail
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

/**
 * Authenticated / mutating call: never cached and always forwards the
 * browser's cookie jar (or whatever `init.headers.cookie` the server page
 * supplied via `authHeaders()`). Use this for `/auth/*`, `/me/*`, `/chat/*`,
 * `/admin/*`, mutations on `/providers/*` and any per-user request.
 */
export async function fetchPrivate<T>(path: string, init?: RequestInit): Promise<T> {
  return executeFetch<T>(path, {
    credentials: 'include',
    ...init,
    cache: 'no-store',
    next: { revalidate: 0 },
    headers: buildHeaders(init),
  });
}

type PublicInit = RequestInit & { revalidate?: number };

/**
 * Cacheable public catalog read. Defaults to a 60s `revalidate` window so
 * Next.js can serve a fresh-enough copy without hitting the API on every
 * request. Pass `{ revalidate: 0 }` to opt out for a specific call site.
 */
export async function fetchPublic<T>(path: string, init?: PublicInit): Promise<T> {
  const { revalidate, ...rest } = init ?? {};
  return executeFetch<T>(path, {
    ...rest,
    next: { revalidate: revalidate ?? 60 },
    headers: buildHeaders(rest),
  });
}

// Internal alias kept while we migrate older code paths. New code MUST pick
// `fetchPrivate` or `fetchPublic` explicitly.
const fetchJson = fetchPrivate;

export async function getApiHealth(): Promise<ApiHealth> {
  try {
    const body = await fetchPublic<{ status: string; version: string }>('/health', {
      revalidate: 0,
    });
    if (body.status !== 'ok') return { ok: false, error: body.status };
    return { ok: true, version: body.version };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'unknown error' };
  }
}

export async function getCategories(): Promise<Category[]> {
  return fetchPublic<Category[]>('/categories', { revalidate: 300 });
}

export async function getCategoryTree(): Promise<CategoryTreeNode[]> {
  return fetchPublic<CategoryTreeNode[]>('/categories/tree', { revalidate: 300 });
}

export async function getCountries(): Promise<Country[]> {
  return fetchPublic<Country[]>('/countries', { revalidate: 600 });
}

export async function getCities(opts: { country?: string; q?: string; limit?: number } = {}): Promise<City[]> {
  const sp = new URLSearchParams();
  if (opts.country) sp.set('country', opts.country);
  if (opts.q) sp.set('q', opts.q);
  if (opts.limit != null) sp.set('limit', String(opts.limit));
  const qs = sp.toString();
  return fetchPublic<City[]>(`/cities${qs ? `?${qs}` : ''}`, { revalidate: opts.q ? 0 : 600 });
}

export async function getLegalForms(country?: string): Promise<LegalForm[]> {
  const qs = country ? `?country=${encodeURIComponent(country)}` : '';
  return fetchPublic<LegalForm[]>(`/legal-forms${qs}`, { revalidate: 600 });
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
  // Catalog listings are public reads; allow Next to serve a 60s-fresh copy.
  return fetchPublic<ProviderListResponse>(`/providers${buildQuery(params)}`);
}

export async function getProvider(slug: string): Promise<ProviderDetail | null> {
  try {
    return await fetchPublic<ProviderDetail>(`/providers/${encodeURIComponent(slug)}`);
  } catch {
    return null;
  }
}

export async function searchProviders(params: ProviderListParams & { q: string }) {
  const qs = buildQuery(params);
  // Search is per-query and emits an analytics event server-side; do not cache.
  return fetchPublic<{
    total: number;
    limit: number;
    offset: number;
    engine: string;
    items: import('./types').ProviderSummary[];
  }>(`/search${qs}`, { revalidate: 0 });
}

export type ProviderSuggestion = {
  slug: string;
  display_name: string;
  description: string | null;
  city_name: string | null;
  country_code: string | null;
};

export async function suggestProviders(
  params: Pick<ProviderListParams, 'categories' | 'countries' | 'cities' | 'legal_forms'> & {
    q: string;
    limit?: number;
  },
): Promise<ProviderSuggestion[]> {
  const qs = buildQuery({ ...params, limit: params.limit ?? 6 });
  const body = await fetchPublic<{ items: ProviderSuggestion[] }>(`/search/suggest${qs}`, {
    revalidate: 0,
  });
  return body.items;
}

// ---- auth ----

export async function login(email: string, password: string): Promise<TokenResponse> {
  return fetchJson<TokenResponse>('/auth/login', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
}

export async function register(
  email: string,
  password: string,
  displayName: string | null,
): Promise<TokenResponse> {
  return fetchJson<TokenResponse>('/auth/register', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export async function logout(): Promise<void> {
  const res = await fetch(`${apiUrl()}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok && res.status !== 204) {
    throw new ApiError(res.status, 'logout failed');
  }
}

export async function getMe(init?: RequestInit): Promise<UserPublic | null> {
  try {
    return await fetchJson<UserPublic>('/auth/me', init);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
}

// ---- chat ----

export async function startConversation(providerSlug: string): Promise<Conversation> {
  return fetchJson<Conversation>('/chat/conversations', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ provider_slug: providerSlug }),
  });
}

export async function listConversations(): Promise<{ total: number; items: Conversation[] }> {
  return fetchJson('/chat/conversations');
}

export async function getConversation(id: string): Promise<Conversation> {
  return fetchJson<Conversation>(`/chat/conversations/${encodeURIComponent(id)}`);
}

export async function listMessages(
  conversationId: string,
  opts?: { limit?: number; before?: string },
): Promise<{ total: number; items: ChatMessage[] }> {
  const sp = new URLSearchParams();
  if (opts?.limit != null) sp.set('limit', String(opts.limit));
  if (opts?.before) sp.set('before', opts.before);
  const qs = sp.toString();
  return fetchJson<{ total: number; items: ChatMessage[] }>(
    `/chat/conversations/${encodeURIComponent(conversationId)}/messages${qs ? `?${qs}` : ''}`,
  );
}

export async function sendMessage(conversationId: string, body: string): Promise<ChatMessage> {
  return fetchJson<ChatMessage>(
    `/chat/conversations/${encodeURIComponent(conversationId)}/messages`,
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ body }),
    },
  );
}

export async function issueWsToken(conversationId: string): Promise<WsTokenResponse> {
  return fetchJson<WsTokenResponse>(
    `/chat/conversations/${encodeURIComponent(conversationId)}/ws-token`,
    { method: 'POST' },
  );
}

// ---- admin analytics ----
//
// These call /admin/* endpoints that require an admin session. The browser
// automatically carries the HttpOnly cookie via `credentials: 'include'`.

type AdminFetchInit = { headers?: Record<string, string> };

export async function getAnalyticsSummary(
  days: number,
  init?: AdminFetchInit,
): Promise<AnalyticsSummary> {
  return fetchJson<AnalyticsSummary>(`/admin/analytics/summary?days=${days}`, init);
}

export async function getTopSearches(
  days: number,
  limit: number,
  init?: AdminFetchInit,
): Promise<TopQueries> {
  return fetchJson<TopQueries>(
    `/admin/analytics/top-searches?days=${days}&limit=${limit}`,
    init,
  );
}

export async function getTopProviders(
  days: number,
  limit: number,
  init?: AdminFetchInit,
): Promise<TopProviders> {
  return fetchJson<TopProviders>(
    `/admin/analytics/top-providers?days=${days}&limit=${limit}`,
    init,
  );
}

// ---- claims ----

export type ClaimInitiateResponse = {
  claim_id: string;
  status: string;
  token: string;
  meta_tag: string;
  instructions: string;
};

export type ClaimPublic = {
  id: string;
  provider_id: string;
  user_id: string;
  status: string;
  method: string;
  verified_at: string | null;
  rejected_at: string | null;
  rejected_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type ProviderUpdate = Partial<{
  display_name: string;
  description: string;
  email: string;
  phone: string;
  address: string;
  logo_url: string;
}>;

export async function initiateClaim(slug: string): Promise<ClaimInitiateResponse> {
  return fetchJson<ClaimInitiateResponse>(
    `/providers/${encodeURIComponent(slug)}/claim`,
    { method: 'POST' },
  );
}

export async function verifyClaim(slug: string): Promise<ClaimPublic> {
  return fetchJson<ClaimPublic>(
    `/providers/${encodeURIComponent(slug)}/claim/verify`,
    { method: 'POST' },
  );
}

export async function listMyClaims(init?: RequestInit): Promise<ClaimPublic[]> {
  return fetchJson<ClaimPublic[]>('/me/claims', init);
}

export async function listMyProviders(init?: RequestInit): Promise<ProviderDetail[]> {
  return fetchJson<ProviderDetail[]>('/me/providers', init);
}

export async function updateOwnedProvider(
  slug: string,
  patch: ProviderUpdate,
): Promise<ProviderDetail> {
  return fetchJson<ProviderDetail>(
    `/providers/${encodeURIComponent(slug)}`,
    {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(patch),
    },
  );
}
