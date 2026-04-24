import Link from 'next/link';
import type { Metadata } from 'next';
import { getCategoryTree } from '@/lib/api';
import { trCategory, trCategoryDescription } from '@/lib/ru';

export const revalidate = 300;
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Категории',
  description: 'Категории услуг для бизнеса в России: ИТ, бухгалтерия, юристы, маркетинг, HR.',
};

export default async function CategoriesPage() {
  const tree = await getCategoryTree();
  const roots = tree.filter((c) => c.parent_id === null);
  return (
    <>
      <div className="hero">
        <h1>Категории</h1>
        <p>Выберите направление и найдите профильных B2B-подрядчиков.</p>
      </div>
      <div className="grid grid-categories">
        {roots.map((c) => (
          <section key={c.id} className="card">
            <h3>
              <Link href={`/providers?country=RU&category=${c.slug}`}>
                {trCategory(c.slug, c.name)}
              </Link>
            </h3>
            {trCategoryDescription(c.slug, c.description) ? (
              <p>{trCategoryDescription(c.slug, c.description)}</p>
            ) : null}
            <div className="meta">
              {c.children.map((child) => (
                <Link
                  key={child.id}
                  href={`/providers?country=RU&category=${child.slug}`}
                  className="chip"
                >
                  {trCategory(child.slug, child.name)}
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
