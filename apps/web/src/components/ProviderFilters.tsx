'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useMemo } from 'react';
import type { FacetValue } from '@/lib/types';
import { trCategory, trCountry, trLegalForm } from '@/lib/ru';

type Props = {
  currentQ: string;
  currentCategories: string[];
  currentCountries: string[];
  currentCities: string[];
  currentLegalForms: string[];
  categories: FacetValue[];
  countries: FacetValue[];
  cities: FacetValue[];
  legalForms: FacetValue[];
};

const GROUPS: ReadonlyArray<{ key: keyof Props; label: string; param: string }> = [
  { key: 'categories', label: 'Категория', param: 'category' },
  { key: 'countries', label: 'Страна', param: 'country' },
  { key: 'cities', label: 'Город', param: 'city' },
  { key: 'legalForms', label: 'Форма компании', param: 'legal_form' },
];

export function ProviderFilters(props: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const current = useMemo<Record<string, Set<string>>>(
    () => ({
      category: new Set(props.currentCategories),
      country: new Set(props.currentCountries),
      city: new Set(props.currentCities),
      legal_form: new Set(props.currentLegalForms),
    }),
    [props.currentCategories, props.currentCountries, props.currentCities, props.currentLegalForms],
  );

  const toggle = useCallback(
    (param: string, value: string) => {
      const sp = new URLSearchParams(searchParams.toString());
      const existing = sp.getAll(param);
      sp.delete(param);
      if (existing.includes(value)) {
        for (const v of existing) {
          if (v !== value) sp.append(param, v);
        }
      } else {
        for (const v of existing) sp.append(param, v);
        sp.append(param, value);
      }
      // reset pagination when filters change
      sp.delete('offset');
      router.push(`${pathname}?${sp.toString()}`);
    },
    [pathname, router, searchParams],
  );

  const clearAll = useCallback(() => {
    const sp = new URLSearchParams();
    if (props.currentQ) sp.set('q', props.currentQ);
    router.push(`${pathname}?${sp.toString()}`);
  }, [pathname, props.currentQ, router]);

  return (
    <div className="filters">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <strong>Фильтры</strong>
        <button
          type="button"
          onClick={clearAll}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          сбросить
        </button>
      </div>
      {GROUPS.map((g) => {
        const values = props[g.key] as FacetValue[];
        if (!values || values.length === 0) {
          // Show a disabled hint so the user still sees the group label.
          return (
            <div key={g.param} className="filter-group">
              <h4>{g.label}</h4>
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Нет вариантов</div>
            </div>
          );
        }
        return (
          <div key={g.param} className="filter-group">
            <h4>{g.label}</h4>
            {values.map((v) => {
              const selected = current[g.param].has(v.value);
              const label =
                g.param === 'category'
                  ? trCategory(v.value, v.label)
                  : g.param === 'country'
                    ? trCountry(v.value.toUpperCase(), v.label)
                    : g.param === 'legal_form'
                      ? trLegalForm(v.value.toUpperCase(), v.label)
                      : v.label;
              return (
                <label key={v.value}>
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => toggle(g.param, v.value)}
                  />
                  <span>{label}</span>
                  <span className="count">{v.count}</span>
                </label>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
