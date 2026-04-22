import { afterEach, describe, expect, it, vi } from 'vitest';
import { getApiHealth } from './api';

describe('getApiHealth', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns ok=true when API responds with 200/ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: 'ok', service: 'ozzb2b-api', version: '0.1.0' }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      ),
    );
    const result = await getApiHealth();
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.version).toBe('0.1.0');
  });

  it('returns ok=false when API responds with non-200', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('err', { status: 500 })),
    );
    const result = await getApiHealth();
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/500/);
  });

  it('returns ok=false on network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('boom')));
    const result = await getApiHealth();
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toBe('boom');
  });
});
