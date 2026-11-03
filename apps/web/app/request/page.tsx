import type { Metadata } from 'next';
import { getCategoryTree, getCities } from '@/lib/api';
import { LeadForm, type LeadFormOption } from '@/components/LeadForm';
import { trCategory, trCity } from '@/lib/ru';

export const metadata: Metadata = {
  title: 'Оставить заявку',
  description:
    'Опишите задачу — мы подберём бухгалтеров, юристов и IT-подрядчиков, которые подходят именно вам. Бесплатно.',
};

export const dynamic = 'force-dynamic';

const DEFAULT_CATEGORY = 'marketplace-accounting';

type SearchParams = { category?: string };

export default async function RequestPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  // Keep the page renderable when the API is down (e2e uses a closed port).
  const [tree, cities] = await Promise.all([
    getCategoryTree().catch(() => []),
    getCities({ country: 'RU', limit: 200 }).catch(() => []),
  ]);

  const categories: LeadFormOption[] = [];
  for (const root of tree.filter((c) => c.parent_id === null)) {
    categories.push({ value: root.slug, label: trCategory(root.slug, root.name) });
    for (const child of root.children) {
      categories.push({
        value: child.slug,
        label: `— ${trCategory(child.slug, child.name)}`,
      });
    }
  }
  if (categories.length === 0) {
    categories.push({ value: DEFAULT_CATEGORY, label: trCategory(DEFAULT_CATEGORY, '') });
  }
  const requested = params.category ?? DEFAULT_CATEGORY;
  const defaultCategory = categories.some((c) => c.value === requested)
    ? requested
    : categories[0].value;

  const cityOptions = cities
    .map((c) => ({ id: c.id, label: trCity(c.name) }))
    .sort((a, b) => a.label.localeCompare(b.label, 'ru'));

  return (
    <>
      <div className="hero">
        <h1>Оставить заявку</h1>
        <p>
          Опишите задачу — мы подберём подходящих подрядчиков и передадим им ваш запрос.
          Бесплатно и без регистрации.
        </p>
      </div>
      <div className="request-layout">
        <LeadForm categories={categories} cities={cityOptions} defaultCategory={defaultCategory} />
        <aside className="request-aside" aria-label="Что будет дальше">
          <ol>
            <li>
              <span className="step-num">1</span>
              <span>
                <strong>Подбираем компании</strong>
                Ищем подрядчиков под ваш запрос в каталоге — обычно в течение рабочего дня.
              </span>
            </li>
            <li>
              <span className="step-num">2</span>
              <span>
                <strong>Отправляем им запрос</strong>
                Только описание задачи. Ваши имя, почта и телефон остаются у нас.
              </span>
            </li>
            <li>
              <span className="step-num">3</span>
              <span>
                <strong>Передаём контакты</strong>
                Тем, кто откликнулся, — и они пишут вам напрямую.
              </span>
            </li>
          </ol>
          <div className="request-note">Бесплатно для вас и для подрядчиков. Без спама.</div>
        </aside>
      </div>
    </>
  );
}
