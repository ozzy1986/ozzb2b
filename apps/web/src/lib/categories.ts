import type { Category } from './types';

function byDisplayOrder(a: Category, b: Category): number {
  return a.position - b.position || a.name.localeCompare(b.name);
}

function uniqueBySlug(categories: Category[]): Category[] {
  const seen = new Set<string>();
  const out: Category[] = [];
  for (const category of categories) {
    if (seen.has(category.slug)) continue;
    seen.add(category.slug);
    out.push(category);
  }
  return out;
}

export function primaryCategories(categories: Category[]): Category[] {
  const roots = categories.filter((category) => category.parent_id === null);
  const visible = roots.length > 0 ? roots : categories;
  return uniqueBySlug([...visible].sort(byDisplayOrder));
}

export function subcategories(categories: Category[]): Category[] {
  return uniqueBySlug(
    categories
      .filter((category) => category.parent_id !== null)
      .sort(byDisplayOrder),
  );
}
