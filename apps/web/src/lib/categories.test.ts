import { describe, expect, it } from 'vitest';
import type { Category } from './types';
import { primaryCategories, subcategories } from './categories';

const category = (patch: Partial<Category> & Pick<Category, 'id' | 'slug' | 'name'>): Category => ({
  parent_id: null,
  description: null,
  position: 10,
  ...patch,
});

describe('category presentation helpers', () => {
  it('shows root categories as primary directions', () => {
    const accounting = category({ id: 1, slug: 'accounting', name: 'Accounting' });
    const bookkeeping = category({
      id: 2,
      parent_id: 1,
      slug: 'bookkeeping',
      name: 'Bookkeeping',
    });

    expect(primaryCategories([bookkeeping, accounting])).toEqual([accounting]);
  });

  it('keeps child categories available as specializations', () => {
    const accounting = category({ id: 1, slug: 'accounting', name: 'Accounting' });
    const bookkeeping = category({
      id: 2,
      parent_id: 1,
      slug: 'bookkeeping',
      name: 'Bookkeeping',
    });

    expect(subcategories([accounting, bookkeeping])).toEqual([bookkeeping]);
  });

  it('falls back to the provided categories when no root is present', () => {
    const uiUx = category({
      id: 3,
      parent_id: 10,
      slug: 'ui-ux-design',
      name: 'UI / UX design',
    });

    expect(primaryCategories([uiUx])).toEqual([uiUx]);
  });
});
