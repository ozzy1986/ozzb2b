import Link from 'next/link';
import { getCategoryTree, listProviders } from '@/lib/api';

export const revalidate = 60;

export default async function HomePage() {
  const [tree, featured] = await Promise.all([
    getCategoryTree().catch(() => []),
    listProviders({ limit: 6 }).catch(() => ({ items: [], total: 0, limit: 6, offset: 0, facets: null })),
  ]);

  const topCategories = tree.filter((c) => c.parent_id === null);

  return (
    <>
      <section className="hero">
        <h1>Find a B2B partner you can trust</h1>
        <p>
          A curated marketplace of outsourcing providers — IT, accounting, legal, marketing, HR.
          Browse verified companies, compare, and get in touch directly.
        </p>
        <form className="search-form" action="/providers" method="get">
          <input
            name="q"
            placeholder="Search companies, services, technologies…"
            aria-label="Search providers"
          />
          <button type="submit">Search</button>
        </form>
      </section>

      <div className="section-head">
        <h2>Browse categories</h2>
        <Link href="/categories">All categories →</Link>
      </div>
      <div className="grid grid-categories">
        {topCategories.map((c) => (
          <Link key={c.id} href={`/providers?category=${encodeURIComponent(c.slug)}`} className="card">
            <h3>{c.name}</h3>
            {c.description ? <p>{c.description}</p> : null}
            <div className="meta">
              {c.children.slice(0, 4).map((child) => (
                <span key={child.id} className="chip">
                  {child.name}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>

      <div className="section-head">
        <h2>Featured providers</h2>
        <Link href="/providers">All providers →</Link>
      </div>
      {featured.items.length === 0 ? (
        <div className="empty">No providers yet. Check back soon.</div>
      ) : (
        <div className="grid grid-providers">
          {featured.items.map((p) => (
            <Link key={p.id} href={`/providers/${p.slug}`} className="card">
              <h3>{p.display_name}</h3>
              {p.description ? <p>{p.description}</p> : null}
              <div className="meta">
                {p.country ? <span className="chip">{p.country.name}</span> : null}
                {p.city ? <span className="chip">{p.city.name}</span> : null}
                {p.categories.slice(0, 3).map((c) => (
                  <span key={c.id} className="chip">
                    {c.name}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
