import type { MetadataRoute } from 'next';
import { getCategories, listProviders } from '@/lib/api';

const BASE_URL = 'https://ozzb2b.com';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const baseEntries: MetadataRoute.Sitemap = [
    { url: `${BASE_URL}/`, lastModified: now, changeFrequency: 'daily', priority: 1 },
    { url: `${BASE_URL}/providers`, lastModified: now, changeFrequency: 'hourly', priority: 0.9 },
    { url: `${BASE_URL}/categories`, lastModified: now, changeFrequency: 'weekly', priority: 0.7 },
  ];

  const [categories, providerData] = await Promise.all([
    getCategories().catch(() => []),
    listProviders({ limit: 500 }).catch(() => ({ items: [], total: 0, limit: 0, offset: 0, facets: null })),
  ]);

  const categoryEntries: MetadataRoute.Sitemap = categories.map((c) => ({
    url: `${BASE_URL}/providers?category=${encodeURIComponent(c.slug)}`,
    lastModified: now,
    changeFrequency: 'weekly',
    priority: 0.5,
  }));
  const providerEntries: MetadataRoute.Sitemap = providerData.items.map((p) => ({
    url: `${BASE_URL}/providers/${p.slug}`,
    lastModified: now,
    changeFrequency: 'weekly',
    priority: 0.6,
  }));

  return [...baseEntries, ...categoryEntries, ...providerEntries];
}
