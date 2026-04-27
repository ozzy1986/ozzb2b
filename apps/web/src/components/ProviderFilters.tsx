'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { getCities } from '@/lib/api';
import type { CategoryTreeNode, City, FacetValue } from '@/lib/types';
import { trCategory, trCity, trCountry, trLegalForm } from '@/lib/ru';

type Props = {
  currentQ: string;
  currentCategories: string[];
  currentCountries: string[];
  currentCities: string[];
  currentLegalForms: string[];
  categoryTree: CategoryTreeNode[];
  categories: FacetValue[];
  countries: FacetValue[];
  cities: FacetValue[];
  legalForms: FacetValue[];
};

type LocationOption = { value: string; label: string };

function switchKeyboardLayout(value: string): string {
  const en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./";
  const ru = "ёйцукенгшщзхъфывапролджэячсмитьбю.";
  const toRu = new Map<string, string>();
  const toEn = new Map<string, string>();
  for (let i = 0; i < en.length; i += 1) {
    toRu.set(en[i], ru[i]);
    toEn.set(ru[i], en[i]);
  }
  let hasRu = false;
  let hasEn = false;
  for (const ch of value.toLowerCase()) {
    if (toEn.has(ch)) hasRu = true;
    if (toRu.has(ch)) hasEn = true;
  }
  const map = hasRu && !hasEn ? toEn : toRu;
  return value
    .toLowerCase()
    .split('')
    .map((ch) => map.get(ch) ?? ch)
    .join('');
}

function queryVariants(raw: string): string[] {
  const base = raw.trim().toLowerCase();
  if (!base) return [];
  const switched = switchKeyboardLayout(base);
  return switched !== base ? [base, switched] : [base];
}

function uniqueOptions(options: LocationOption[]): LocationOption[] {
  const seen = new Set<string>();
  const out: LocationOption[] = [];
  for (const option of options) {
    if (seen.has(option.value)) continue;
    seen.add(option.value);
    out.push(option);
  }
  return out;
}

function cityToOption(city: City): LocationOption {
  return { value: city.slug, label: trCity(city.name) };
}

export function ProviderFilters(props: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeCountry = props.currentCountries[0];
  const [countryQuery, setCountryQuery] = useState(activeCountry ?? '');
  const [cityQuery, setCityQuery] = useState(props.currentCities[0] ?? '');
  const [citySuggestions, setCitySuggestions] = useState<LocationOption[]>([]);

  const current = useMemo<Record<string, Set<string>>>(
    () => ({
      category: new Set(props.currentCategories),
      country: new Set(props.currentCountries),
      city: new Set(props.currentCities),
      legal_form: new Set(props.currentLegalForms),
    }),
    [props.currentCategories, props.currentCountries, props.currentCities, props.currentLegalForms],
  );

  const categoryCounts = useMemo(
    () => new Map(props.categories.map((facet) => [facet.value, facet.count])),
    [props.categories],
  );

  const countryOptions = useMemo(
    () =>
      props.countries.map((country) => ({
        value: country.value,
        label: trCountry(country.value.toUpperCase(), country.label),
      })),
    [props.countries],
  );

  const countryOptionsWithCurrent = useMemo(() => {
    if (!activeCountry) return countryOptions;
    if (countryOptions.some((option) => option.value === activeCountry)) return countryOptions;
    return [{ value: activeCountry, label: activeCountry }, ...countryOptions];
  }, [activeCountry, countryOptions]);

  const cityOptions = useMemo(
    () => uniqueOptions([
      ...citySuggestions,
      ...props.cities.map((city) => ({
        value: city.value,
        label: trCity(city.label),
      })),
    ]),
    [citySuggestions, props.cities],
  );

  useEffect(() => {
    const normalized = cityQuery.trim().toLowerCase();
    if (normalized.length < 2) {
      setCitySuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      const variants = queryVariants(normalized);
      void Promise.all(
        variants.map((variant) =>
          getCities({ country: activeCountry, q: variant, limit: 20 }).catch(() => []),
        ),
      )
        .then((batches) => setCitySuggestions(uniqueOptions(batches.flat().map(cityToOption))))
        .catch(() => setCitySuggestions([]));
    }, 200);
    return () => window.clearTimeout(timer);
  }, [activeCountry, cityQuery]);

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

  const setSingle = useCallback(
    (param: string, value: string | null) => {
      const sp = new URLSearchParams(searchParams.toString());
      sp.delete(param);
      if (value) sp.append(param, value);
      if (param === 'country') sp.delete('city');
      sp.delete('offset');
      router.push(`${pathname}?${sp.toString()}`);
    },
    [pathname, router, searchParams],
  );

  const applyAutocomplete = useCallback(
    (param: 'country' | 'city', raw: string, options: Array<{ value: string; label: string }>) => {
      const normalized = raw.trim().toLowerCase();
      if (!normalized) {
        setSingle(param, null);
        return;
      }
      const variants = queryVariants(normalized);
      const match =
        options.find((option) =>
          variants.some(
            (variant) =>
              option.label.toLowerCase() === variant || option.value.toLowerCase() === variant,
          ),
        ) ||
        options.find((option) =>
          variants.some(
            (variant) =>
              option.label.toLowerCase().startsWith(variant) ||
              option.value.toLowerCase().startsWith(variant),
          ),
        ) ||
        options.find((option) =>
          variants.some(
            (variant) =>
              option.label.toLowerCase().includes(variant) ||
              option.value.toLowerCase().includes(variant),
          ),
        );
      if (match) setSingle(param, match.value);
    },
    [setSingle],
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
      <div className="filter-group">
        <h4>Категории</h4>
        {props.categoryTree.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Нет вариантов</div>
        ) : (
          <div className="category-tree">
            {props.categoryTree.map((parent) => {
              const parentSelected = current.category.has(parent.slug);
              const parentCount = categoryCounts.get(parent.slug);
              return (
                <div key={parent.id} className="category-parent">
                  <label>
                    <input
                      type="checkbox"
                      checked={parentSelected}
                      onChange={() => toggle('category', parent.slug)}
                    />
                    <span>{trCategory(parent.slug, parent.name)}</span>
                    {parentCount != null ? <span className="count">{parentCount}</span> : null}
                  </label>
                  {parent.children.length > 0 ? (
                    <div className="category-children">
                      {parent.children.map((child) => (
                        <label key={child.id}>
                          <input
                            type="checkbox"
                            checked={current.category.has(child.slug)}
                            onChange={() => toggle('category', child.slug)}
                          />
                          <span>{trCategory(child.slug, child.name)}</span>
                        </label>
                      ))}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="filter-group">
        <h4>Страна</h4>
        <select
          className="filter-select"
          value={activeCountry ?? ''}
          onChange={(e) => {
            const value = e.target.value;
            setCountryQuery(value);
            setSingle('country', value || null);
          }}
        >
          <option value="">Все страны</option>
          {countryOptionsWithCurrent.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <div className="filter-actions">
          <button
            type="button"
            onClick={() => applyAutocomplete('country', countryQuery, countryOptions)}
          >
            Применить
          </button>
          <button type="button" onClick={() => setSingle('country', null)}>
            Сбросить
          </button>
        </div>
      </div>

      <div className="filter-group">
        <h4>Город</h4>
        <input
          className="filter-select"
          list="city-filter-options"
          placeholder="Начните вводить город..."
          value={cityQuery}
          onChange={(e) => setCityQuery(e.target.value)}
          onBlur={(e) => applyAutocomplete('city', e.target.value, cityOptions)}
        />
        <datalist id="city-filter-options">
          {cityOptions.map((option) => (
            <option key={option.value} value={option.label} />
          ))}
        </datalist>
        <div className="filter-actions">
          <button type="button" onClick={() => applyAutocomplete('city', cityQuery, cityOptions)}>
            Применить
          </button>
          <button type="button" onClick={() => setSingle('city', null)}>
            Сбросить
          </button>
        </div>
      </div>

      <div className="filter-group">
        <h4>Форма компании</h4>
        {props.legalForms.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Нет вариантов</div>
        ) : (
          props.legalForms.map((value) => (
            <label key={value.value}>
              <input
                type="checkbox"
                checked={current.legal_form.has(value.value)}
                onChange={() => toggle('legal_form', value.value)}
              />
              <span>{trLegalForm(value.value.toUpperCase(), value.label)}</span>
              <span className="count">{value.count}</span>
            </label>
          ))
        )}
      </div>
    </div>
  );
}
