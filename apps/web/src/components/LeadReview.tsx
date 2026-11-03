'use client';

import { useState } from 'react';
import Link from '@/components/AppLink';
import {
  addOutreach,
  bulkOutreach,
  sendOutreach,
  skipOutreach,
  updateLead,
  updateOutreach,
  type OutreachBulkAction,
} from '@/lib/api';
import { humanizeDetail, humanizeError } from '@/lib/errors';
import { LEAD_STATUS_LABEL, OUTREACH_STATUS_LABEL } from '@/lib/leads';
import type { LeadDetail, LeadStatus, OutreachMessage } from '@/lib/types';
import { ErrorAlert } from './ErrorAlert';

type Draft = { to_email: string; subject: string; body: string };

function draftOf(m: OutreachMessage): Draft {
  return { to_email: m.to_email, subject: m.subject, body: m.body };
}

function isDirty(m: OutreachMessage, d: Draft | undefined): boolean {
  return !!d && (d.to_email !== m.to_email || d.subject !== m.subject || d.body !== m.body);
}

const isEditable = (m: OutreachMessage) => m.status === 'draft' || m.status === 'failed';
// Sent messages stay as a record of what went out.
const isSelectable = (m: OutreachMessage) => m.status !== 'sent';

export function LeadReview({ initial }: { initial: LeadDetail }) {
  const [lead, setLead] = useState(initial);
  const [messages, setMessages] = useState<OutreachMessage[]>(initial.outreach);
  // Unsaved edits live here (not in each editor) so bulk send can save them first.
  const [edits, setEdits] = useState<Record<string, Draft>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkBusy, setBulkBusy] = useState(false);
  const [note, setNote] = useState(initial.admin_note ?? '');
  const [providerSlug, setProviderSlug] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const selectable = messages.filter(isSelectable);
  const chosen = messages.filter((m) => selected.has(m.id) && isSelectable(m));
  const chosenSendable = chosen.filter(isEditable);
  const allChosen = selectable.length > 0 && chosen.length === selectable.length;

  function replace(updated: OutreachMessage) {
    setMessages((list) => list.map((m) => (m.id === updated.id ? updated : m)));
    setEdits(({ [updated.id]: _, ...rest }) => rest);
    if (!isSelectable(updated)) toggle(updated.id, false);
  }

  function edit(id: string, draft: Draft) {
    setEdits((all) => ({ ...all, [id]: draft }));
  }

  function toggle(id: string, on: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleAll(on: boolean) {
    setSelected(on ? new Set(selectable.map((m) => m.id)) : new Set());
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

  async function runBulk(action: OutreachBulkAction) {
    const targets = action === 'send' ? chosenSendable : chosen;
    if (targets.length === 0) return;
    const question =
      action === 'send'
        ? `Отправить писем: ${targets.length}?`
        : `Удалить писем: ${targets.length}? Это нельзя отменить.`;
    if (!window.confirm(question)) return;

    setError(null);
    setNotice(null);
    setBulkBusy(true);
    try {
      if (action === 'send') {
        for (const m of targets) {
          const d = edits[m.id];
          if (isDirty(m, d)) replace(await updateOutreach(m.id, d!));
        }
      }
      const results = await bulkOutreach(
        lead.id,
        action,
        targets.map((m) => m.id),
      );
      const removed = new Set<string>();
      const problems: string[] = [];
      for (const r of results) {
        if (r.message) replace(r.message);
        if (action === 'delete' && r.ok) removed.add(r.id);
        if (!r.ok) {
          const name = messages.find((m) => m.id === r.id)?.provider.display_name ?? r.id;
          // Send failures keep the SMTP text on the card; domain errors get translated.
          problems.push(`${name}: ${r.message ? 'ошибка отправки' : humanizeDetail(r.error ?? '', 'outreach')}`);
        }
      }
      if (removed.size > 0) {
        setMessages((list) => list.filter((m) => !removed.has(m.id)));
        setSelected((prev) => new Set([...prev].filter((id) => !removed.has(id))));
      }
      const done = results.length - problems.length;
      setNotice(action === 'send' ? `Отправлено: ${done}.` : `Удалено: ${done}.`);
      if (problems.length > 0) setError(`Не получилось (${problems.length}): ${problems.join('; ')}`);
    } catch (err) {
      setError(humanizeError(err, 'outreach'));
    } finally {
      setBulkBusy(false);
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

      <section style={{ display: 'grid', gap: 16 }}>
        <h2>Письма подрядчикам ({messages.length})</h2>
        {selectable.length > 0 ? (
          <div className="sidebar-card bulk-bar">
            <label className="bulk-check">
              <input
                type="checkbox"
                checked={allChosen}
                onChange={(e) => toggleAll(e.target.checked)}
                disabled={bulkBusy}
              />
              Выбрать все
            </label>
            <span className="bulk-count">Выбрано: {chosen.length}</span>
            <button
              type="button"
              className="contact-cta"
              disabled={bulkBusy || chosenSendable.length === 0}
              onClick={() => runBulk('send')}
            >
              {bulkBusy ? 'Выполняем...' : `Отправить (${chosenSendable.length})`}
            </button>
            <button
              type="button"
              className="chip"
              disabled={bulkBusy || chosen.length === 0}
              onClick={() => runBulk('delete')}
            >
              Удалить ({chosen.length})
            </button>
          </div>
        ) : null}
        {notice ? (
          <div className="auth-hint" role="status">
            {notice}
          </div>
        ) : null}
        <ErrorAlert message={error} />
        {messages.length === 0 ? (
          <div className="empty">
            Подходящих компаний с почтой не нашлось. Добавьте компанию вручную ниже.
          </div>
        ) : (
          messages.map((m) => (
            <OutreachEditor
              key={m.id}
              message={m}
              draft={edits[m.id] ?? draftOf(m)}
              selected={selected.has(m.id)}
              locked={bulkBusy}
              onSelect={(on) => toggle(m.id, on)}
              onEdit={(d) => edit(m.id, d)}
              onChange={replace}
              onError={setError}
            />
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
  draft,
  selected,
  locked,
  onSelect,
  onEdit,
  onChange,
  onError,
}: {
  message: OutreachMessage;
  draft: Draft;
  selected: boolean;
  locked: boolean;
  onSelect: (on: boolean) => void;
  onEdit: (d: Draft) => void;
  onChange: (m: OutreachMessage) => void;
  onError: (e: string | null) => void;
}) {
  const [pending, setPending] = useState(false);
  const editable = isEditable(message);
  const dirty = isDirty(message, draft);
  const busy = pending || locked;

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
    return updateOutreach(message.id, draft);
  }

  async function saveAndSend(): Promise<OutreachMessage> {
    if (dirty) onChange(await save());
    return sendOutreach(message.id);
  }

  return (
    <article className="sidebar-card form-card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <strong style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {isSelectable(message) ? (
            <input
              type="checkbox"
              aria-label={`Выбрать: ${message.provider.display_name}`}
              checked={selected}
              disabled={locked}
              onChange={(e) => onSelect(e.target.checked)}
              style={{ width: 'auto' }}
            />
          ) : null}
          <span>
            <Link href={`/providers/${message.provider.slug}`}>{message.provider.display_name}</Link>
            {message.provider.website ? (
              <>
                {' · '}
                <a href={message.provider.website} target="_blank" rel="noopener noreferrer">
                  сайт
                </a>
              </>
            ) : null}
          </span>
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
          value={draft.to_email}
          onChange={(e) => onEdit({ ...draft, to_email: e.target.value })}
          disabled={!editable}
        />
      </label>
      <label>
        <div>Тема</div>
        <input
          value={draft.subject}
          maxLength={255}
          onChange={(e) => onEdit({ ...draft, subject: e.target.value })}
          disabled={!editable}
        />
      </label>
      <label>
        <div>Текст</div>
        <textarea
          rows={14}
          value={draft.body}
          onChange={(e) => onEdit({ ...draft, body: e.target.value })}
          disabled={!editable}
        />
      </label>
      {editable ? (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="contact-cta"
            disabled={busy}
            onClick={() => {
              if (window.confirm(`Отправить письмо на ${draft.to_email}?`)) void run(saveAndSend);
            }}
          >
            {pending ? 'Отправляем...' : 'Отправить'}
          </button>
          <button type="button" className="chip" disabled={busy || !dirty} onClick={() => run(save)}>
            Сохранить черновик
          </button>
          <button
            type="button"
            className="chip"
            disabled={busy}
            onClick={() => run(() => skipOutreach(message.id))}
          >
            Не отправлять
          </button>
        </div>
      ) : null}
    </article>
  );
}
