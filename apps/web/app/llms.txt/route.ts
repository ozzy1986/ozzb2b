import { NICHE, CITY_GEO, SITE_URL, listAllProviders, nicheCitySlugs } from '@/lib/seo';

export const revalidate = 3600;

/** llms.txt (llmstxt.org): a plain map of the site for AI assistants. */
export async function GET() {
  const niche = await listAllProviders({ categories: [NICHE.category] }).catch(() => []);
  const cities = nicheCitySlugs(niche);

  const lines = [
    '# ozzb2b',
    '',
    '> Каталог B2B-подрядчиков в России и бесплатный подбор исполнителей по заявке. ' +
      'Основная ниша сейчас — бухгалтерия для селлеров маркетплейсов (Wildberries, Ozon, Яндекс Маркет).',
    '',
    'Клиент описывает задачу, ozzb2b отбирает подходящие компании и отправляет им описание без контактов клиента; ' +
      'контакты получают только откликнувшиеся. Для клиента и подрядчиков это бесплатно.',
    '',
    '## Основные страницы',
    '',
    `- [${NICHE.name}](${SITE_URL}${NICHE.path}): бухгалтеры для селлеров, что входит в услуги, частые вопросы о налогах и стоимости`,
    `- [Оставить заявку](${SITE_URL}/request): форма подбора подрядчика`,
    `- [Каталог компаний](${SITE_URL}/providers): все подрядчики с фильтрами по услугам и городам`,
    `- [Категории услуг](${SITE_URL}/categories)`,
    '',
  ];
  if (cities.length > 0) {
    lines.push('## Бухгалтерия для маркетплейсов по городам', '');
    for (const slug of cities) {
      lines.push(`- [${CITY_GEO[slug].name}](${SITE_URL}${NICHE.path}/${slug})`);
    }
    lines.push('');
  }
  if (niche.length > 0) {
    lines.push('## Бухгалтерии для селлеров в каталоге', '');
    for (const p of niche) {
      const city = p.city?.slug && CITY_GEO[p.city.slug] ? `, ${CITY_GEO[p.city.slug].name}` : '';
      const about = p.description ? `: ${p.description.replace(/\s+/g, ' ').slice(0, 160)}` : '';
      lines.push(`- [${p.display_name}${city}](${SITE_URL}/providers/${p.slug})${about}`);
    }
    lines.push('');
  }

  return new Response(lines.join('\n'), {
    headers: { 'content-type': 'text/plain; charset=utf-8' },
  });
}
