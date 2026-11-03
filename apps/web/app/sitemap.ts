import type { MetadataRoute } from 'next';
import { getCategories } from '@/lib/api';
import { NICHE, SITE_URL, listAllProviders, nicheCitySlugs } from '@/lib/seo';

export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const [categories, providers, niche] = await Promise.all([
    getCategories().catch(() => []),
    listAllProviders({ countries: ['RU'] }).catch(() => []),
    listAllProviders({ categories: [NICHE.category] }).catch(() => []),
  ]);

  const base: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: 'daily', priority: 1 },
    { url: `${SITE_URL}${NICHE.path}`, lastModified: now, changeFrequency: 'weekly', priority: 0.95 },
    { url: `${SITE_URL}/providers`, lastModified: now, changeFrequency: 'daily', priority: 0.8 },
    { url: `${SITE_URL}/categories`, lastModified: now, changeFrequency: 'weekly', priority: 0.6 },
    { url: `${SITE_URL}/request`, lastModified: now, changeFrequency: 'monthly', priority: 0.7 },
  ];

  const cityPages: MetadataRoute.Sitemap = nicheCitySlugs(niche).map((slug) => ({
    url: `${SITE_URL}${NICHE.path}/${slug}`,
    lastModified: now,
    changeFrequency: 'weekly',
    priority: 0.85,
  }));

  // Same URL shape the listing declares as canonical for a single category.
  const categoryPages: MetadataRoute.Sitemap = categories.map((c) => ({
    url: `${SITE_URL}/providers?category=${encodeURIComponent(c.slug)}`,
    lastModified: now,
    changeFrequency: 'weekly',
    priority: 0.5,
  }));

  const providerPages: MetadataRoute.Sitemap = providers.map((p) => ({
    url: `${SITE_URL}/providers/${p.slug}`,
    lastModified: p.last_scraped_at ? new Date(p.last_scraped_at) : now,
    changeFrequency: 'weekly',
    priority: 0.6,
  }));

  return [...base, ...cityPages, ...categoryPages, ...providerPages];
}
