'use client';

import { useState } from 'react';
import Link from '@/components/AppLink';
import {
  addOutreach,
  sendOutreach,
  skipOutreach,
  updateLead,
  updateOutreach,
} from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { LEAD_STATUS_LABEL, OUTREACH_STATUS_LABEL } from '@/lib/leads';
import type { LeadDetail, LeadStatus, OutreachMessage } from '@/lib/types';
import { ErrorAlert } from './ErrorAlert';

export function LeadReview({ initial }: { initial: LeadDetail }) {
  const [lead, setLead] = useState(initial);
  const [messages, setMessages] = useState<OutreachMessage[]>(initial.outreach);
  const [note, setNote] = useState(initial.admin_note ?? '');
  const [providerSlug, setProviderSlug] = useState('');
  const [error, setError] = useState<string | null>(null);

  function replace(updated: OutreachMessage) {
    setMessages((list) => list.map((m) => (m.id === updated.id ? updated : m)));
  }

  async function saveLead(patch: { status?: LeadStatus; admin_note?: string }) {
    setError(null);
    try {
      const updated = await updateLead(lead.id, patch);
      setLead(updated);
    } catch (err) {
      setError(humanizeError(err, 'outreach'));
    }
  }

  async function onAddProvider(ev: React.FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    setError(null);
    const slug = providerSlug.trim().replace(/^.*\/providers\//, '').replace(/\/$/, '');
    if (!slug) return;
    try {
      const created = await addOutreach(lead.id, slug);
      setMessages((list) => [...list, created]);
      setProviderSlug('');
    } catch (err) {
      setError(humanizeError(err, 'outreach'));
    }
  }

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <section className="sidebar-card form-card" style={{ display: 'grid', gap: 12 }}>
        <h3>Запрос клиента</h3>
        <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{lead.description}</p>
        <dl>
          <dt>Клиент</dt>
          <dd>
            {lead.contact_name}
            {lead.company_name ? `, ${lead.company_name}` : ''}
          </dd>
          <dt>Почта</dt>
          <dd>
            <a href={`mailto:${lead.contact_email}`}>{lead.contact_email}</a>
          </dd>
          {lead.contact_phone ? (
            <>
              <dt>Телефон</dt>
              <dd>{lead.contact_phone}</dd>
            </>
          ) : null}
        </dl>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
            Статус:
            <select
              value={lead.status}
              onChange={(e) => saveLead({ status: e.target.value as LeadStatus })}
              style={{ width: 'auto' }}
            >
              {Object.entries(LEAD_STATUS_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          <div>Заметка для себя</div>
          <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <div>
          <button type="button" className="chip" onClick={() => saveLead({ admin_note: note })}>
            Сохранить заметку
          </button>
        </div>
      </section>

      <ErrorAlert message={error} />

      <section style={{ display: 'grid', gap: 16 }}>
        <h2>Письма подрядчикам ({messages.length})</h2>
        {messages.length === 0 ? (
          <div className="empty">
            Подходящих компаний с почтой не нашлось. Добавьте компанию вручную ниже.
          </div>
        ) : (
          messages.map((m) => (
            <OutreachEditor key={m.id} message={m} onChange={replace} onError={setError} />
          ))
        )}
        <form onSubmit={onAddProvider} className="sidebar-card form-card" style={{ display: 'grid', gap: 8 }}>
          <label>
            <div>Добавить компанию (адрес её страницы в каталоге или slug)</div>
            <input
              value={providerSlug}
              onChange={(e) => setProviderSlug(e.target.value)}
              placeholder="https://ozzb2b.com/providers/..."
            />
          </label>
          <div>
            <button type="submit" className="chip">
              Создать черновик
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function OutreachEditor({
  message,
  onChange,
  onError,
}: {
  message: OutreachMessage;
  onChange: (m: OutreachMessage) => void;
  onError: (e: string | null) => void;
}) {
  const [toEmail, setToEmail] = useState(message.to_email);
  const [subject, setSubject] = useState(message.subject);
  const [body, setBody] = useState(message.body);
  const [pending, setPending] = useState(false);
  const editable = message.status === 'draft' || message.status === 'failed';
  const dirty =
    toEmail !== message.to_email || subject !== message.subject || body !== message.body;

  async function run(action: () => Promise<OutreachMessage>) {
    onError(null);
    setPending(true);
    try {
      onChange(await action());
    } catch (err) {
      onError(humanizeError(err, 'outreach'));
    } finally {
      setPending(false);
    }
  }

  async function save(): Promise<OutreachMessage> {
    return updateOutreach(message.id, { to_email: toEmail, subject, body });
  }

  async function saveAndSend(): Promise<OutreachMessage> {
    if (dirty) await save();
    return sendOutreach(message.id);
  }

  return (
    <article className="sidebar-card form-card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <strong>
          <Link href={`/providers/${message.provider.slug}`}>{message.provider.display_name}</Link>
          {message.provider.website ? (
            <>
              {' · '}
              <a href={message.provider.website} target="_blank" rel="noopener noreferrer">
                сайт
              </a>
            </>
          ) : null}
        </strong>
        <span className="chip">
          {OUTREACH_STATUS_LABEL[message.status]}
          {message.sent_at ? ` ${new Date(message.sent_at).toLocaleString('ru-RU')}` : ''}
        </span>
      </div>
      {message.error ? <ErrorAlert message={`Ошибка отправки: ${message.error}`} /> : null}
      <label>
        <div>Кому</div>
        <input
          type="email"
          value={toEmail}
          onChange={(e) => setToEmail(e.target.value)}
          disabled={!editable}
        />
      </label>
      <label>
        <div>Тема</div>
        <input
          value={subject}
          maxLength={255}
          onChange={(e) => setSubject(e.target.value)}
          disabled={!editable}
        />
      </label>
      <label>
        <div>Текст</div>
        <textarea
          rows={14}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          disabled={!editable}
        />
      </label>
      {editable ? (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="contact-cta"
            disabled={pending}
            onClick={() => {
              if (window.confirm(`Отправить письмо на ${toEmail}?`)) void run(saveAndSend);
            }}
          >
            {pending ? 'Отправляем...' : 'Отправить'}
          </button>
          <button type="button" className="chip" disabled={pending || !dirty} onClick={() => run(save)}>
            Сохранить черновик
          </button>
          <button
            type="button"
            className="chip"
            disabled={pending}
            onClick={() => run(() => skipOutreach(message.id))}
          >
            Не отправлять
          </button>
        </div>
      ) : null}
    </article>
  );
}
