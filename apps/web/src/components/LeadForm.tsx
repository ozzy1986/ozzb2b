'use client';

import { useEffect, useState } from 'react';
import { createLead, getLeadFormToken, type LeadCreate } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { ErrorAlert } from './ErrorAlert';

export type LeadFormOption = { value: string; label: string };

type Props = {
  categories: LeadFormOption[];
  cities: { id: number; label: string }[];
  defaultCategory: string;
};

type Fields = Omit<LeadCreate, 'form_token' | 'city_id' | 'consent'> & { city_id: string };

export function LeadForm({ categories, cities, defaultCategory }: Props) {
  const [fields, setFields] = useState<Fields>({
    category_slug: defaultCategory,
    city_id: '',
    description: '',
    budget: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    company_name: '',
    website: '',
  });
  const [consent, setConsent] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLeadFormToken()
      .then(setToken)
      .catch((err) => setError(humanizeError(err, 'lead-submit')));
  }, []);

  function set<K extends keyof Fields>(key: K, value: Fields[K]) {
    setFields((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(ev: React.FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    if (!token) return;
    setError(null);
    setPending(true);
    try {
      await createLead({
        ...fields,
        city_id: fields.city_id ? Number(fields.city_id) : null,
        budget: fields.budget || null,
        contact_phone: fields.contact_phone || null,
        company_name: fields.company_name || null,
        consent,
        form_token: token,
      });
      setDone(true);
    } catch (err) {
      setError(humanizeError(err, 'lead-submit'));
      // A fresh token lets the visitor retry without reloading the page.
      getLeadFormToken().then(setToken).catch(() => undefined);
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <div className="sidebar-card" role="status">
        <h2>Заявка отправлена</h2>
        <p>
          Мы подберём подходящих подрядчиков и свяжемся с вами по указанной почте. Обычно это
          занимает один рабочий день.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="sidebar-card form-card" style={{ display: 'grid', gap: 12 }}>
      <label>
        <div>Что нужно</div>
        <select
          name="category_slug"
          value={fields.category_slug}
          onChange={(e) => set('category_slug', e.target.value)}
          required
        >
          {categories.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        <div>Опишите задачу</div>
        <textarea
          name="description"
          rows={6}
          minLength={20}
          maxLength={4000}
          required
          placeholder="Например: ИП на УСН 6%, продаём на Wildberries и Ozon, оборот около 2 млн ₽ в месяц. Нужен бухгалтер на постоянное сопровождение."
          value={fields.description}
          onChange={(e) => set('description', e.target.value)}
        />
      </label>
      <div className="lead-form-row">
        <label>
          <div>Город</div>
          <select
            name="city_id"
            value={fields.city_id}
            onChange={(e) => set('city_id', e.target.value)}
          >
            <option value="">Не важно, можно удалённо</option>
            {cities.map((c) => (
              <option key={c.id} value={String(c.id)}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <div>Бюджет (необязательно)</div>
          <input
            name="budget"
            maxLength={120}
            placeholder="до 15 000 ₽ в месяц"
            value={fields.budget ?? ''}
            onChange={(e) => set('budget', e.target.value)}
          />
        </label>
      </div>
      <div className="lead-form-row">
        <label>
          <div>Как к вам обращаться</div>
          <input
            name="contact_name"
            required
            minLength={2}
            maxLength={120}
            autoComplete="name"
            value={fields.contact_name}
            onChange={(e) => set('contact_name', e.target.value)}
          />
        </label>
        <label>
          <div>Компания или ИП (необязательно)</div>
          <input
            name="company_name"
            maxLength={255}
            autoComplete="organization"
            value={fields.company_name ?? ''}
            onChange={(e) => set('company_name', e.target.value)}
          />
        </label>
      </div>
      <div className="lead-form-row">
        <label>
          <div>Электронная почта</div>
          <input
            type="email"
            name="contact_email"
            required
            maxLength={255}
            autoComplete="email"
            value={fields.contact_email}
            onChange={(e) => set('contact_email', e.target.value)}
          />
        </label>
        <label>
          <div>Телефон (необязательно)</div>
          <input
            type="tel"
            name="contact_phone"
            maxLength={64}
            autoComplete="tel"
            value={fields.contact_phone ?? ''}
            onChange={(e) => set('contact_phone', e.target.value)}
          />
        </label>
      </div>
      {/* Honeypot: invisible to people, bots fill every field they find. */}
      <div aria-hidden="true" style={{ position: 'absolute', left: '-10000px', height: 0, overflow: 'hidden' }}>
        <label>
          Сайт
          <input
            name="website"
            tabIndex={-1}
            autoComplete="off"
            value={fields.website}
            onChange={(e) => set('website', e.target.value)}
          />
        </label>
      </div>
      <label style={{ flexDirection: 'row', gap: 8, alignItems: 'flex-start', color: 'var(--text)' }}>
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          required
          style={{ width: 'auto', marginTop: 4 }}
        />
        <span>
          Согласен, что описание задачи будет передано подходящим подрядчикам, а мои контакты —
          тем, кто откликнется.
        </span>
      </label>
      <div>
        <button type="submit" className="contact-cta" disabled={pending || !token}>
          {pending ? 'Отправляем...' : 'Отправить заявку'}
        </button>
      </div>
      <ErrorAlert message={error} />
    </form>
  );
}
