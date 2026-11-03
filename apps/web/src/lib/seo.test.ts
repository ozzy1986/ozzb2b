import { describe, expect, it, vi } from 'vitest';
import type { ProviderSummary } from './types';

vi.mock('./api', () => ({ listProviders: vi.fn() }));

import { listProviders } from './api';
import { groupByCity, jsonLd, listAllProviders, nicheCitySlugs } from './seo';

function provider(slug: string, city: string | null): ProviderSummary {
  return {
    slug,
    city: city ? { slug: city, name: city } : null,
  } as unknown as ProviderSummary;
}

describe('city pages', () => {
  const list = [
    provider('a', 'moscow'),
    provider('b', 'moscow'),
    provider('c', 'moscow'),
    provider('d', 'kazan'),
    provider('e', 'kazan'),
    provider('f', 'perm'),
    provider('g', 'atlantis'),
    provider('h', null),
  ];

  it('groups only cities we can name in Russian', () => {
    const groups = groupByCity(list);
    expect([...groups.keys()].sort()).toEqual(['kazan', 'moscow', 'perm']);
  });

  it('skips thin cities and orders by size', () => {
    expect(nicheCitySlugs(list)).toEqual(['moscow', 'kazan']);
  });
});

describe('listAllProviders', () => {
  it('pages past the API limit of 100', async () => {
    const mocked = vi.mocked(listProviders);
    const page = (n: number, offset: number) =>
      Array.from({ length: n }, (_, i) => provider(`p${offset + i}`, null));
    mocked.mockImplementation(async (p) => {
      const offset = p?.offset ?? 0;
      expect(p?.limit).toBe(100);
      const items = offset === 0 ? page(100, 0) : page(30, offset);
      return { items, total: 130, limit: 100, offset, facets: null };
    });
    const all = await listAllProviders({ categories: ['x'] });
    expect(all).toHaveLength(130);
    expect(mocked).toHaveBeenCalledTimes(2);
  });
});

describe('jsonLd', () => {
  it('cannot be broken out of a script tag', () => {
    const out = jsonLd({ name: '</script><script>alert(1)</script>' }).__html;
    expect(out).not.toContain('</script>');
    expect(JSON.parse(out).name).toBe('</script><script>alert(1)</script>');
  });
});
