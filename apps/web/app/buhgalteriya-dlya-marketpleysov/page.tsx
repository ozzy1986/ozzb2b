import type { Metadata } from 'next';
import { NicheLanding } from '@/components/NicheLanding';
import { NICHE, groupByCity, listAllProviders, nicheCitySlugs } from '@/lib/seo';

export const revalidate = 3600;

export const metadata: Metadata = {
  title: { absolute: 'Бухгалтерия для маркетплейсов — бухгалтер для селлеров WB и Ozon | ozzb2b' },
  description:
    'Бухгалтер для селлера Wildberries, Ozon и Яндекс Маркета: учёт продаж по отчётам площадок, УСН и НДС, отчётность ИП и ООО. Подборка компаний и бесплатный подбор по заявке.',
  alternates: { canonical: NICHE.path },
  openGraph: {
    title: 'Бухгалтерия для маркетплейсов',
    description: 'Бухгалтеры для селлеров Wildberries и Ozon: подборка компаний и бесплатный подбор.',
    url: NICHE.path,
  },
};

export default async function MarketplaceAccountingPage() {
  const providers = await listAllProviders({ categories: [NICHE.category] }).catch(() => []);
  const byCity = groupByCity(providers);
  const cities = nicheCitySlugs(providers).map((slug) => ({
    slug,
    count: byCity.get(slug)?.length ?? 0,
  }));
  return <NicheLanding providers={providers} cities={cities} />;
}
