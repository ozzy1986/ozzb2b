import Link from 'next/link';
import { getCategoryTree, listProviders } from '@/lib/api';
import { trCategory, trCategoryDescription, trCity, trCountry } from '@/lib/ru';
import { primaryCategories } from '@/lib/categories';
import { ProviderSearchBox } from '@/components/ProviderSearchBox';

export const revalidate = 60;

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
      <section className="hero">
        <h1>Найдите надежного B2B-подрядчика в России</h1>
        <p>
          Каталог проверенных компаний: ИТ, бухгалтерия, юридические, маркетинговые и HR-услуги.
          Сравнивайте исполнителей и связывайтесь напрямую.
        </p>
        <ProviderSearchBox countries={['RU']} />
      </section>

      <div className="section-head">
        <h2>Категории услуг</h2>
        <Link href="/categories">Все категории →</Link>
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

      <div className="section-head">
        <h2>Рекомендуемые компании</h2>
        <Link href="/providers?country=RU">Все компании →</Link>
      </div>
      {featured.items.length === 0 ? (
        <div className="empty">Компании еще добавляются. Загляните чуть позже.</div>
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
                    <span key={c.id} className="chip">
                      {trCategory(c.slug, c.name)}
                    </span>
                  ))}
                {p.country ? (
                  <span className="chip">{trCountry(p.country.code, p.country.name)}</span>
                ) : null}
                {p.city ? <span className="chip">{trCity(p.city.name)}</span> : null}
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
