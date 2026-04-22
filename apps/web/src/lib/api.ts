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

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiUrl()}${path}`, {
    credentials: 'include',
    ...init,
    cache: 'no-store',
    next: { revalidate: 0 },
    headers: {
      accept: 'application/json',
      ...(init?.headers ?? {}),
    },
  });
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
