import { describe, expect, it } from 'vitest';
import {
  freshnessLabel,
  trCategory,
  trCategoryDescription,
  trCity,
  trCountry,
  trLegalForm,
} from './ru';

describe('translations', () => {
  it('translates known categories and falls back for unknown', () => {
    expect(trCategory('it', 'IT')).toBe('ИТ и разработка');
    expect(trCategory('unknown', 'Other')).toBe('Other');
  });

  it('translates countries with fallback', () => {
    expect(trCountry('RU', 'Russia')).toBe('Россия');
    expect(trCountry('US', 'USA')).toBe('USA');
    expect(trCountry(undefined, 'fallback')).toBe('fallback');
  });

  it('translates legal forms with fallback', () => {
    expect(trLegalForm('OOO', 'OOO')).toBe('ООО');
    expect(trLegalForm(undefined, 'x')).toBe('x');
  });

  it('returns category description only when known', () => {
    expect(trCategoryDescription('it', null)).toContain('Разработка');
    expect(trCategoryDescription('unknown', 'fallback')).toBe('fallback');
  });

  it('translates city names', () => {
    expect(trCity('Moscow')).toBe('Москва');
    expect(trCity('Unknown City')).toBe('Unknown City');
  });
});

describe('freshnessLabel', () => {
  const NOW = Date.now();
  const iso = (offsetMs: number) => new Date(NOW - offsetMs).toISOString();

  it('returns null for null/invalid/future values', () => {
    expect(freshnessLabel(null)).toBeNull();
    expect(freshnessLabel(undefined)).toBeNull();
    expect(freshnessLabel('garbage')).toBeNull();
    expect(
      freshnessLabel(new Date(NOW + 60_000).toISOString()),
    ).toBeNull();
  });

  it('formats minutes/hours/days with correct Russian pluralization', () => {
    expect(freshnessLabel(iso(30_000))).toBe('Обновлено только что');
    expect(freshnessLabel(iso(60_000))).toMatch(/1 минуту/);
    expect(freshnessLabel(iso(3 * 60_000))).toMatch(/3 минуты/);
    expect(freshnessLabel(iso(25 * 60_000))).toMatch(/25 минут/);
    expect(freshnessLabel(iso(60 * 60_000))).toMatch(/1 час/);
    expect(freshnessLabel(iso(3 * 60 * 60_000))).toMatch(/3 часа/);
    expect(freshnessLabel(iso(10 * 60 * 60_000))).toMatch(/10 часов/);
    expect(freshnessLabel(iso(24 * 60 * 60_000))).toMatch(/1 день/);
    expect(freshnessLabel(iso(5 * 24 * 60 * 60_000))).toMatch(/5 дней/);
  });

  it('formats months and years for older timestamps', () => {
    expect(freshnessLabel(iso(35 * 24 * 60 * 60_000))).toMatch(/месяц/);
    expect(freshnessLabel(iso(2 * 365 * 24 * 60 * 60_000))).toMatch(/год|лет/);
  });
});
