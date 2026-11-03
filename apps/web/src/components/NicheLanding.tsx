import Link from '@/components/AppLink';
import { Breadcrumbs, type Crumb } from '@/components/Breadcrumbs';
import { primaryCategories } from '@/lib/categories';
import { trCategory, trCity } from '@/lib/ru';
import { CITY_GEO, NICHE, SITE_URL, jsonLd } from '@/lib/seo';
import type { ProviderSummary } from '@/lib/types';

const SERVICES = [
  {
    title: 'Учёт продаж с площадок',
    text: 'Разбор отчётов Wildberries, Ozon и Яндекс Маркета: реализация, комиссии, логистика, штрафы и возвраты.',
  },
  {
    title: 'Налоги и режим',
    text: 'Выбор между УСН 6%, УСН 15% и ОСНО, расчёт авансов, контроль порога по НДС.',
  },
  {
    title: 'Отчётность',
    text: 'Декларации, КУДиР, отчёты в ФНС и фонды. Для ООО — бухгалтерская отчётность.',
  },
  {
    title: 'Товарный учёт',
    text: 'Себестоимость, остатки на складах маркетплейсов, маркировка «Честный знак».',
  },
  {
    title: 'Сотрудники',
    text: 'Зарплата, кадровые документы и отчёты по сотрудникам, если они есть.',
  },
  {
    title: 'Восстановление учёта',
    text: 'Если учёт запущен: сверка с площадками и налоговой, уточнённые декларации.',
  },
];

const FAQ = [
  {
    q: 'Чем бухгалтерия для маркетплейсов отличается от обычной?',
    a: 'Деньги приходят от площадки одним платежом за вычетом комиссий, логистики и штрафов, а продажи нужно учитывать по отчётам о реализации. Бухгалтер, который работает с селлерами, умеет разбирать эти отчёты и правильно считать доход для налога.',
  },
  {
    q: 'Какой налоговый режим выбрать селлеру?',
    a: 'Чаще всего — УСН. «Доходы» (6%) проще, но налог считается со всей выручки, включая комиссии площадки. «Доходы минус расходы» (15%) выгоднее при высокой себестоимости и больших комиссиях. Выбор лучше сделать вместе с бухгалтером по реальным цифрам.',
  },
  {
    q: 'Нужно ли платить НДС на упрощёнке?',
    a: 'Да, если доход превышает порог, установленный Налоговым кодексом. С 2025 года плательщики УСН с доходом выше порога стали плательщиками НДС, и порог постепенно снижается. Бухгалтер следит за выручкой и заранее предупреждает о переходе.',
  },
  {
    q: 'Сколько стоит бухгалтер для селлера?',
    a: 'Зависит от формы (ИП или ООО), налогового режима, количества площадок, операций и сотрудников. Обслуживание ИП на УСН без сотрудников обычно стоит несколько тысяч рублей в месяц, ООО с НДС и складом — заметно дороже. Точную цену подрядчики называют после описания задачи.',
  },
  {
    q: 'Можно ли работать с бухгалтером из другого города?',
    a: 'Да. Отчёты площадок, банк и ЭДО доступны онлайн, поэтому большинство бухгалтерий для селлеров работает удалённо по всей России.',
  },
  {
    q: 'Как ozzb2b подбирает подрядчика?',
    a: 'Вы описываете задачу в заявке, мы отбираем компании, которые работают с маркетплейсами, и отправляем им описание без ваших контактов. Контакты получают только те, кто откликнулся. Для вас это бесплатно.',
  },
];

type Props = {
  providers: ProviderSummary[];
  /** Cities that have their own page, with how many companies each lists. */
  cities: { slug: string; count: number }[];
  city?: string;
};

export function NicheLanding({ providers, cities, city }: Props) {
  const geo = city ? CITY_GEO[city] : undefined;
  const where = geo ? geo.prepositional : 'по всей России';
  const pagePath = geo ? `${NICHE.path}/${city}` : NICHE.path;
  const requestHref = `/request?category=${NICHE.category}`;

  const crumbs: Crumb[] = [
    { label: 'Главная', href: '/' },
    geo ? { label: NICHE.name, href: NICHE.path } : { label: NICHE.name },
    ...(geo ? [{ label: geo.name }] : []),
  ];

  const structured = [
    {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: FAQ.map((f) => ({
        '@type': 'Question',
        name: f.q,
        acceptedAnswer: { '@type': 'Answer', text: f.a },
      })),
    },
    {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: `${NICHE.name} ${where}`,
      url: `${SITE_URL}${pagePath}`,
      numberOfItems: providers.length,
      itemListElement: providers.map((p, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        url: `${SITE_URL}/providers/${p.slug}`,
        name: p.display_name,
      })),
    },
  ];

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={jsonLd(structured)} />
      <Breadcrumbs items={crumbs} />

      <section className="hero hero-home" style={{ paddingTop: 8 }}>
        <span className="hero-badge">
          <b>Wildberries · Ozon · Яндекс Маркет</b>
          {providers.length} {plural(providers.length, 'компания', 'компании', 'компаний')} в подборке
        </span>
        <h1>
          {geo ? `Бухгалтерия для маркетплейсов ${geo.prepositional}` : 'Бухгалтерия для маркетплейсов'}
        </h1>
        <p>
          {geo
            ? `Бухгалтеры для селлеров ${geo.prepositional}: ведут учёт продаж на Wildberries и Ozon, считают налоги и сдают отчётность. Выберите компанию сами или оставьте заявку — подберём бесплатно.`
            : 'Бухгалтер для селлера Wildberries, Ozon и Яндекс Маркета: учёт продаж по отчётам площадок, налоги на УСН и ОСНО, отчётность для ИП и ООО. Выберите компанию сами или оставьте заявку — подберём бесплатно.'}
        </p>
        <div className="hero-actions">
          <Link href={requestHref} className="btn btn-primary btn-lg">
            Подобрать бухгалтера
          </Link>
          <a href="#companies" className="btn btn-ghost btn-lg">
            Смотреть компании ↓
          </a>
        </div>
      </section>

      <section className="section" style={{ marginTop: 72 }}>
        <div className="section-title">
          <h2>Что делает бухгалтер для селлера</h2>
          <p>Обычная бухгалтерия не всегда понимает отчёты площадок. Здесь — те, кто понимает.</p>
        </div>
        <div className="grid grid-categories">
          {SERVICES.map((s) => (
            <div key={s.title} className="card" style={{ cursor: 'default' }}>
              <h3>{s.title}</h3>
              <p style={{ WebkitLineClamp: 'unset' }}>{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section" id="companies">
        <div className="section-title">
          <h2>
            {geo ? `Бухгалтерии для селлеров ${geo.prepositional}` : 'Бухгалтерии для селлеров'}
          </h2>
          <p>
            Компании, которые прямо пишут о работе с маркетплейсами. Данные собраны с их сайтов
            и регулярно обновляются.
          </p>
        </div>
        {providers.length === 0 ? (
          <div className="empty">Компании ещё добавляются. Оставьте заявку — подберём вручную.</div>
        ) : (
          <div className="grid grid-providers">
            {providers.map((p) => (
              <Link key={p.id} href={`/providers/${p.slug}`} className="card">
                <h3>{p.display_name}</h3>
                {p.description ? <p>{p.description}</p> : null}
                <div className="meta">
                  {primaryCategories(p.categories)
                    .slice(0, 1)
                    .map((c) => (
                      <span key={c.id} className="chip chip-accent">
                        {trCategory(c.slug, c.name)}
                      </span>
                    ))}
                  {p.city ? <span className="chip">{trCity(p.city.name)}</span> : null}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {cities.length > 0 ? (
        <section className="section">
          <div className="section-title">
            <h2>По городам</h2>
            <p>Большинство бухгалтерий работает удалённо, но кому-то важно встретиться лично.</p>
          </div>
          <nav className="city-links" aria-label="Города">
            {geo ? (
              <Link href={NICHE.path} className="chip">
                Вся Россия
              </Link>
            ) : null}
            {cities.map((c) => (
              <Link
                key={c.slug}
                href={`${NICHE.path}/${c.slug}`}
                className={c.slug === city ? 'chip chip-accent' : 'chip'}
                aria-current={c.slug === city ? 'page' : undefined}
              >
                {CITY_GEO[c.slug].name} <span style={{ opacity: 0.6 }}>{c.count}</span>
              </Link>
            ))}
          </nav>
        </section>
      ) : null}

      <section className="section">
        <div className="section-title">
          <h2>Частые вопросы</h2>
        </div>
        <div className="faq">
          {FAQ.map((f) => (
            <details key={f.q}>
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="cta-panel">
        <div>
          <h2>Не хотите выбирать сами?</h2>
          <p>
            Опишите, на каких площадках продаёте и какой у вас режим, — передадим запрос
            подходящим бухгалтериям. Бесплатно.
          </p>
        </div>
        <Link href={requestHref} className="btn btn-light btn-lg">
          Оставить заявку
        </Link>
      </section>
    </>
  );
}

function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}
