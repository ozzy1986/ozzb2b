const API_URL = process.env.OZZB2B_API_URL ?? process.env.NEXT_PUBLIC_OZZB2B_API_URL ?? 'http://localhost:8001';

export type ApiHealth =
  | { ok: true; version: string }
  | { ok: false; error: string };

export async function getApiHealth(): Promise<ApiHealth> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: 'no-store', next: { revalidate: 0 } });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const body = (await res.json()) as { status: string; version: string };
    if (body.status !== 'ok') return { ok: false, error: body.status };
    return { ok: true, version: body.version };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'unknown error' };
  }
}
