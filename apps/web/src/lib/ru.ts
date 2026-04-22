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
