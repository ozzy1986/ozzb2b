'use client';

import { useState } from 'react';
import {
  updateOwnedProvider,
  type ProviderUpdate,
} from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import type { ProviderDetail } from '@/lib/types';
import { ErrorAlert } from './ErrorAlert';

type Props = {
  initial: ProviderDetail;
};

export function OwnedProviderEditor({ initial }: Props) {
  const [form, setForm] = useState<ProviderUpdate>({
    display_name: initial.display_name,
    description: initial.description ?? '',
    email: initial.email ?? '',
    phone: initial.phone ?? '',
    address: initial.address ?? '',
    logo_url: initial.logo_url ?? '',
  });
  const [saved, setSaved] = useState<Date | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function onChange<K extends keyof ProviderUpdate>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(ev: React.FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    setError(null);
    setPending(true);
    try {
      await updateOwnedProvider(initial.slug, form);
      setSaved(new Date());
    } catch (err) {
      setError(humanizeError(err, 'provider-update'));
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="sidebar-card" style={{ display: 'grid', gap: 12 }}>
      <label>
        <div>Название</div>
        <input
          name="display_name"
          value={form.display_name ?? ''}
          onChange={(e) => onChange('display_name', e.target.value)}
          required
          maxLength={255}
        />
      </label>
      <label>
        <div>Описание</div>
        <textarea
          name="description"
          rows={5}
          maxLength={4000}
          value={form.description ?? ''}
          onChange={(e) => onChange('description', e.target.value)}
        />
      </label>
      <label>
        <div>Электронная почта для клиентов</div>
        <input
          type="email"
          name="email"
          maxLength={255}
          value={form.email ?? ''}
          onChange={(e) => onChange('email', e.target.value)}
        />
      </label>
      <label>
        <div>Телефон</div>
        <input
          name="phone"
          maxLength={64}
          value={form.phone ?? ''}
          onChange={(e) => onChange('phone', e.target.value)}
        />
      </label>
      <label>
        <div>Адрес</div>
        <input
          name="address"
          maxLength={500}
          value={form.address ?? ''}
          onChange={(e) => onChange('address', e.target.value)}
        />
      </label>
      <label>
        <div>Ссылка на логотип (URL)</div>
        <input
          name="logo_url"
          maxLength={500}
          value={form.logo_url ?? ''}
          onChange={(e) => onChange('logo_url', e.target.value)}
        />
      </label>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button type="submit" className="contact-cta" disabled={pending}>
          {pending ? 'Сохраняем...' : 'Сохранить'}
        </button>
        {saved ? (
          <span className="auth-hint">
            Сохранено в {saved.toLocaleTimeString('ru-RU')}
          </span>
        ) : null}
      </div>
      <ErrorAlert message={error} />
    </form>
  );
}
