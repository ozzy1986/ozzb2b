'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { suggestProviders, type ProviderSuggestion } from '@/lib/api';
import { trCity, trCountry } from '@/lib/ru';

type Props = {
  currentQ?: string;
  countries?: string[];
  categories?: string[];
  cities?: string[];
  legalForms?: string[];
};

export function ProviderSearchBox({
  currentQ = '',
  countries = ['RU'],
  categories = [],
  cities = [],
  legalForms = [],
}: Props) {
  const [q, setQ] = useState(currentQ);
  const [suggestions, setSuggestions] = useState<ProviderSuggestion[]>([]);
  const trimmed = q.trim();
  const suggestionParams = useMemo(
    () => ({ countries, categories, cities, legal_forms: legalForms }),
    [categories, cities, countries, legalForms],
  );

  useEffect(() => {
    if (trimmed.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      void suggestProviders({ ...suggestionParams, q: trimmed, limit: 6 })
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [suggestionParams, trimmed]);

  return (
    <div className="smart-search">
      <form className="search-form" action="/providers" method="get">
        {countries.map((country) => (
          <input key={country} type="hidden" name="country" value={country} />
        ))}
        {categories.map((category) => (
          <input key={category} type="hidden" name="category" value={category} />
        ))}
        {cities.map((city) => (
          <input key={city} type="hidden" name="city" value={city} />
        ))}
        {legalForms.map((legalForm) => (
          <input key={legalForm} type="hidden" name="legal_form" value={legalForm} />
        ))}
        <input
          name="q"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="Поиск по названию, услугам, городу..."
          aria-label="Поиск компаний"
          autoComplete="off"
        />
        <button type="submit">Искать</button>
      </form>
      {suggestions.length > 0 ? (
        <div className="search-suggestions" role="listbox" aria-label="Подсказки поиска">
          {suggestions.map((item) => (
            <Link key={item.slug} href={`/providers/${item.slug}`} role="option">
              <strong>{item.display_name}</strong>
              <span>
                {[item.country_code ? trCountry(item.country_code, item.country_code) : null, item.city_name ? trCity(item.city_name) : null]
                  .filter(Boolean)
                  .join(', ')}
              </span>
              {item.description ? <small>{item.description}</small> : null}
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}
