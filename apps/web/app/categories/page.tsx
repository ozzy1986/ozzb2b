import Link from 'next/link';
import type { Metadata } from 'next';
import { getCategoryTree } from '@/lib/api';

export const revalidate = 300;

export const metadata: Metadata = {
  title: 'Categories',
  description: 'Browse service categories: IT, accounting, legal, marketing, HR.',
};

export default async function CategoriesPage() {
  const tree = await getCategoryTree();
  const roots = tree.filter((c) => c.parent_id === null);
  return (
    <>
      <div className="hero">
        <h1>Categories</h1>
        <p>Pick an area to find outsourcing providers specialized in it.</p>
      </div>
      <div className="grid grid-categories">
        {roots.map((c) => (
          <section key={c.id} className="card">
            <h3>
              <Link href={`/providers?category=${c.slug}`}>{c.name}</Link>
            </h3>
            {c.description ? <p>{c.description}</p> : null}
            <div className="meta">
              {c.children.map((child) => (
                <Link key={child.id} href={`/providers?category=${child.slug}`} className="chip">
                  {child.name}
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
