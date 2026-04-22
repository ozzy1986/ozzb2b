const CATEGORY_RU: Record<string, string> = {
  it: 'ИТ',
  'software-development': 'Разработка ПО',
  'devops-cloud': 'DevOps и облака',
  'quality-assurance': 'Тестирование',
  'data-analytics': 'Данные и аналитика',
  'ai-ml': 'AI / ML',
  cybersecurity: 'Кибербезопасность',
  'ui-ux-design': 'UI / UX дизайн',
  accounting: 'Бухгалтерия',
  bookkeeping: 'Бухучет',
  'tax-advisory': 'Налоговый консалтинг',
  payroll: 'Расчет зарплаты',
  'audit-assurance': 'Аудит',
  'financial-reporting': 'Финансовая отчетность',
  legal: 'Юридические услуги',
  'corporate-law': 'Корпоративное право',
  contracts: 'Договорное право',
  'intellectual-property': 'Интеллектуальная собственность',
  'compliance-regulatory': 'Комплаенс и регуляторика',
  'dispute-resolution': 'Разрешение споров',
  'labor-law': 'Трудовое право',
  marketing: 'Маркетинг',
  seo: 'SEO',
  content: 'Контент-маркетинг',
  'paid-media': 'Платный трафик',
  branding: 'Брендинг',
  pr: 'PR и коммуникации',
  hr: 'HR',
  recruiting: 'Подбор персонала',
  staffing: 'Аутстаффинг',
  'eor-peo': 'EOR / PEO',
  training: 'Обучение и развитие',
};

const CATEGORY_DESCRIPTION_RU: Record<string, string> = {
  it: 'Разработка ПО, DevOps, QA, аналитика данных, AI/ML, кибербезопасность, дизайн.',
  accounting:
    'Бухучет, налоги, зарплатные проекты, аудит и финансовая отчетность для бизнеса.',
  legal: 'Корпоративное право, договоры, ИС, комплаенс и разрешение споров.',
  marketing: 'Digital-маркетинг, SEO, контент, PR, брендинг и performance-реклама.',
  hr: 'Подбор персонала, аутстаффинг, EOR/PEO, обучение и развитие команд.',
};

const COUNTRY_RU: Record<string, string> = {
  RU: 'Россия',
};

const LEGAL_FORM_RU: Record<string, string> = {
  OOO: 'ООО',
  AO: 'АО',
  PAO: 'ПАО',
  IP: 'ИП',
  UNK: 'Не указано',
  SELF_EMPLOYED: 'Самозанятый',
};

const CITY_RU_BY_EN: Record<string, string> = {
  Moscow: 'Москва',
  'Saint Petersburg': 'Санкт-Петербург',
  Novosibirsk: 'Новосибирск',
  Yekaterinburg: 'Екатеринбург',
  Kazan: 'Казань',
  'Nizhny Novgorod': 'Нижний Новгород',
  Samara: 'Самара',
  Ulyanovsk: 'Ульяновск',
  Voronezh: 'Воронеж',
  Omsk: 'Омск',
  Kirov: 'Киров',
  Perm: 'Пермь',
  'Rostov-on-Don': 'Ростов-на-Дону',
  Krasnodar: 'Краснодар',
};

export function trCategory(slug: string, fallback: string): string {
  return CATEGORY_RU[slug] ?? fallback;
}

export function trCountry(code: string | undefined, fallback: string): string {
  if (!code) return fallback;
  return COUNTRY_RU[code] ?? fallback;
}

export function trLegalForm(code: string | undefined, fallback: string): string {
  if (!code) return fallback;
  return LEGAL_FORM_RU[code] ?? fallback;
}

export function trCategoryDescription(slug: string, fallback: string | null): string | null {
  return CATEGORY_DESCRIPTION_RU[slug] ?? fallback;
}

export function trCity(name: string): string {
  return CITY_RU_BY_EN[name] ?? name;
}

/** Human-friendly "data freshness" label, e.g. "Обновлено 3 дня назад".
 *
 * Returns null when the input is null / unparseable so the UI can skip the
 * badge entirely instead of showing "Invalid date".
 */
export function freshnessLabel(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const ts = Date.parse(iso);
  if (Number.isNaN(ts)) return null;
  const diffMs = Date.now() - ts;
  if (diffMs < 0) return null;
  const minutes = Math.floor(diffMs / 60_000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (minutes < 1) return 'Обновлено только что';
  if (minutes < 60) return `Обновлено ${minutes} ${plural(minutes, ['минуту', 'минуты', 'минут'])} назад`;
  if (hours < 24) return `Обновлено ${hours} ${plural(hours, ['час', 'часа', 'часов'])} назад`;
  if (days < 30) return `Обновлено ${days} ${plural(days, ['день', 'дня', 'дней'])} назад`;
  const months = Math.floor(days / 30);
  if (months < 12) return `Обновлено ${months} ${plural(months, ['месяц', 'месяца', 'месяцев'])} назад`;
  const years = Math.floor(months / 12);
  return `Обновлено ${years} ${plural(years, ['год', 'года', 'лет'])} назад`;
}

function plural(n: number, forms: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return forms[0];
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return forms[1];
  return forms[2];
}
