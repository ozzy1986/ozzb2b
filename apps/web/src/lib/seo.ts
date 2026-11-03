import { listProviders, type ProviderListParams } from './api';
import type { ProviderSummary } from './types';

export const SITE_URL = 'https://ozzb2b.com';

/** The niche we are building search traffic for first. */
export const NICHE = {
  category: 'marketplace-accounting',
  path: '/buhgalteriya-dlya-marketpleysov',
  name: 'Бухгалтерия для маркетплейсов',
} as const;

/**
 * City pages only exist for cities with at least this many niche providers:
 * a page listing one company is thin content and search engines treat it so.
 */
export const MIN_PROVIDERS_FOR_CITY_PAGE = 2;

type CityGeo = { name: string; prepositional: string };

/** City slug (as stored by the API) → Russian name and "в …" form. */
export const CITY_GEO: Record<string, CityGeo> = {
  moscow: { name: 'Москва', prepositional: 'в Москве' },
  'saint-petersburg': { name: 'Санкт-Петербург', prepositional: 'в Санкт-Петербурге' },
  kazan: { name: 'Казань', prepositional: 'в Казани' },
  tyumen: { name: 'Тюмень', prepositional: 'в Тюмени' },
  yekaterinburg: { name: 'Екатеринбург', prepositional: 'в Екатеринбурге' },
  'nizhny-novgorod': { name: 'Нижний Новгород', prepositional: 'в Нижнем Новгороде' },
  novosibirsk: { name: 'Новосибирск', prepositional: 'в Новосибирске' },
  samara: { name: 'Самара', prepositional: 'в Самаре' },
  perm: { name: 'Пермь', prepositional: 'в Перми' },
  'rostov-on-don': { name: 'Ростов-на-Дону', prepositional: 'в Ростове-на-Дону' },
  voronezh: { name: 'Воронеж', prepositional: 'в Воронеже' },
  chelyabinsk: { name: 'Челябинск', prepositional: 'в Челябинске' },
  ufa: { name: 'Уфа', prepositional: 'в Уфе' },
  krasnodar: { name: 'Краснодар', prepositional: 'в Краснодаре' },
};

/** The API caps `limit` at 100; walk the pages to get everything. */
export async function listAllProviders(
  params: Omit<ProviderListParams, 'limit' | 'offset'> = {},
  max = 2000,
): Promise<ProviderSummary[]> {
  const pageSize = 100;
  const out: ProviderSummary[] = [];
  for (let offset = 0; offset < max; offset += pageSize) {
    const page = await listProviders({ ...params, limit: pageSize, offset });
    out.push(...page.items);
    if (page.items.length < pageSize || out.length >= page.total) break;
  }
  return out;
}

/** Niche providers grouped by city slug, only for cities we can name in Russian. */
export function groupByCity(providers: ProviderSummary[]): Map<string, ProviderSummary[]> {
  const byCity = new Map<string, ProviderSummary[]>();
  for (const p of providers) {
    const slug = p.city?.slug;
    if (!slug || !CITY_GEO[slug]) continue;
    byCity.set(slug, [...(byCity.get(slug) ?? []), p]);
  }
  return byCity;
}

export function nicheCitySlugs(providers: ProviderSummary[]): string[] {
  return [...groupByCity(providers).entries()]
    .filter(([, list]) => list.length >= MIN_PROVIDERS_FOR_CITY_PAGE)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([slug]) => slug);
}

export function jsonLd(data: unknown): { __html: string } {
  // `<` escaped so a provider description can never close the script tag.
  return { __html: JSON.stringify(data).replace(/</g, '\\u003c') };
}
