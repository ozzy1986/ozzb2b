import Link from '@/components/AppLink';
import { getCategoryTree, listProviders } from '@/lib/api';
import { trCategory, trCategoryDescription, trCity, trCountry } from '@/lib/ru';
import { primaryCategories } from '@/lib/categories';
import { ProviderSearchBox } from '@/components/ProviderSearchBox';

export const revalidate = 60;

const STEPS = [
  {
    title: 'Опишите задачу',
    text: 'Пара абзацев о том, что нужно: налоговый режим, площадки, объём. Регистрация не нужна.',
  },
  {
    title: 'Мы подберём подрядчиков',
    text: 'Находим компании под ваш запрос и вручную отправляем им описание — без ваших контактов.',
  },
  {
    title: 'Подрядчики напишут вам',
    text: 'Ваши контакты получат только те, кто откликнулся. Сравнивайте и выбирайте сами.',
  },
];

export default async function HomePage() {
  const [tree, featured] = await Promise.all([
    getCategoryTree().catch(() => []),
    listProviders({ countries: ['RU'], limit: 6 }).catch(() => ({
      items: [],
      total: 0,
      limit: 6,
      offset: 0,
      facets: null,
    })),
  ]);

  const topCategories = tree.filter((c) => c.parent_id === null);

  return (
    <>
      <section className="hero hero-home">
        <Link href="/request?category=marketplace-accounting" className="hero-badge">
          <b>Новое</b>
          Бухгалтерия для селлеров Wildberries и Ozon →
        </Link>
        <h1>
          Найдём надёжного <span style={{ whiteSpace: 'nowrap' }}>B2B-подрядчика</span> для
          вашего бизнеса
        </h1>
        <p>
          Бухгалтерия, юристы, IT и маркетинг. Опишите задачу — подберём компании, которые
          подходят именно вам. Бесплатно.
        </p>
        <div className="hero-actions">
          <Link href="/request" className="btn btn-primary btn-lg">
            Оставить заявку
          </Link>
          <Link href="/providers?country=RU" className="btn btn-ghost btn-lg">
            Смотреть компании →
          </Link>
        </div>
        <div className="hero-search">
          <ProviderSearchBox countries={['RU']} />
          <div className="hero-search-hint">Или найдите сами: по названию, услуге или городу</div>
        </div>
      </section>

      <section className="band" aria-labelledby="how-it-works">
        <Arcs />
        <div className="container">
          <div className="band-window">
            <div className="band-window-bar" aria-hidden>
              <i />
              <i />
              <i />
              <span>ozzb2b.com/request</span>
            </div>
            <h2 id="how-it-works" className="visually-hidden">
              Как это работает
            </h2>
            <ol className="steps" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {STEPS.map((s, i) => (
                <li key={s.title} className="step">
                  <span className="step-num">{i + 1}</span>
                  <h3>{s.title}</h3>
                  <p>{s.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-title">
          <h2>Категории услуг</h2>
          <p>Начали с бухгалтерии для маркетплейсов — постепенно добавляем другие направления.</p>
        </div>
        <div className="grid grid-categories">
          {topCategories.map((c) => (
            <Link
              key={c.id}
              href={`/providers?country=RU&category=${encodeURIComponent(c.slug)}`}
              className="card"
            >
              <h3>{trCategory(c.slug, c.name)}</h3>
              {trCategoryDescription(c.slug, c.description) ? (
                <p>{trCategoryDescription(c.slug, c.description)}</p>
              ) : null}
              <div className="meta">
                {c.children.slice(0, 4).map((child) => (
                  <span key={child.id} className="chip">
                    {trCategory(child.slug, child.name)}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
        <div className="section-more">
          <Link href="/categories" className="btn btn-ghost">
            Все категории →
          </Link>
        </div>
      </section>

      <section className="section">
        <div className="section-title">
          <h2>Компании в каталоге</h2>
          <p>Собираем подрядчиков из открытых источников и проверяем, чем они занимаются.</p>
        </div>
        {featured.items.length === 0 ? (
          <div className="empty">Компании ещё добавляются. Загляните чуть позже.</div>
        ) : (
          <div className="grid grid-providers">
            {featured.items.map((p) => (
              <Link key={p.id} href={`/providers/${p.slug}`} className="card">
                <h3>{p.display_name}</h3>
                {p.description ? <p>{p.description}</p> : null}
                <div className="meta">
                  {primaryCategories(p.categories)
                    .slice(0, 2)
                    .map((c) => (
                      <span key={c.id} className="chip chip-accent">
                        {trCategory(c.slug, c.name)}
                      </span>
                    ))}
                  {p.city ? (
                    <span className="chip">{trCity(p.city.name)}</span>
                  ) : p.country ? (
                    <span className="chip">{trCountry(p.country.code, p.country.name)}</span>
                  ) : null}
                </div>
              </Link>
            ))}
          </div>
        )}
        <div className="section-more">
          <Link href="/providers?country=RU" className="btn btn-ghost">
            Все компании →
          </Link>
        </div>
      </section>

      <section className="cta-panel">
        <Arcs light />
        <div>
          <h2>Не хотите искать сами?</h2>
          <p>Опишите задачу за пару минут — подберём подрядчиков и передадим им ваш запрос.</p>
        </div>
        <Link href="/request" className="btn btn-light btn-lg">
          Оставить заявку
        </Link>
      </section>
    </>
  );
}

/** Decorative sweeping arcs behind the green band and the closing panel. */
function Arcs({ light = false }: { light?: boolean }) {
  const stroke = light ? 'rgba(255,255,255,0.18)' : 'rgba(34,87,63,0.28)';
  return (
    <svg
      className="band-arcs"
      viewBox="0 0 1440 600"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden
    >
      <path d="M-80 520 C 300 120, 700 80, 1520 -60" stroke={stroke} strokeWidth="56" fill="none" />
      <path d="M180 700 C 520 360, 980 300, 1560 260" stroke={stroke} strokeWidth="28" fill="none" />
      <path d="M980 -40 C 1080 200, 1260 360, 1520 420" stroke={stroke} strokeWidth="40" fill="none" />
    </svg>
  );
}
