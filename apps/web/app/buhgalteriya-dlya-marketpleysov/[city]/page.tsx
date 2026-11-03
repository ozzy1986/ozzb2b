import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { NicheLanding } from '@/components/NicheLanding';
import { CITY_GEO, NICHE, groupByCity, listAllProviders, nicheCitySlugs } from '@/lib/seo';

export const revalidate = 3600;

type RouteParams = Promise<{ city: string }>;

async function loadCity(city: string) {
  if (!CITY_GEO[city]) return null;
  const providers = await listAllProviders({ categories: [NICHE.category] }).catch(() => []);
  const slugs = nicheCitySlugs(providers);
  if (!slugs.includes(city)) return null;
  const byCity = groupByCity(providers);
  return {
    providers: byCity.get(city) ?? [],
    cities: slugs.map((slug) => ({ slug, count: byCity.get(slug)?.length ?? 0 })),
  };
}

export async function generateMetadata({ params }: { params: RouteParams }): Promise<Metadata> {
  const { city } = await params;
  const geo = CITY_GEO[city];
  if (!geo) return { title: 'Страница не найдена' };
  const title = `Бухгалтерия для маркетплейсов ${geo.prepositional} — бухгалтер для селлеров WB и Ozon`;
  return {
    title: { absolute: `${title} | ozzb2b` },
    description: `Бухгалтеры для селлеров ${geo.prepositional}: учёт продаж на Wildberries и Ozon, налоги на УСН и НДС, отчётность ИП и ООО. Компании с контактами и бесплатный подбор по заявке.`,
    alternates: { canonical: `${NICHE.path}/${city}` },
    openGraph: { title, url: `${NICHE.path}/${city}` },
  };
}

export default async function MarketplaceAccountingCityPage({ params }: { params: RouteParams }) {
  const { city } = await params;
  const data = await loadCity(city);
  if (!data) notFound();
  return <NicheLanding providers={data.providers} cities={data.cities} city={city} />;
}
