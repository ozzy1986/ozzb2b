'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { listConversations } from '@/lib/api';
import { humanizeError, isApiErrorStatus } from '@/lib/errors';
import type { Conversation } from '@/lib/types';
import { ErrorAlert } from '../ErrorAlert';

type Props = {
  activeConversationId: string | null;
  /** When true, render only the list of conversations without a surrounding hero. */
  compact?: boolean;
};

function formatTimestamp(iso: string | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

export function ChatInbox({ activeConversationId, compact }: Props) {
  const router = useRouter();
  const [state, setState] = useState<
    | { status: 'loading' }
    | { status: 'empty' }
    | { status: 'error'; message: string }
    | { status: 'ready'; items: Conversation[] }
  >({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await listConversations();
        if (cancelled) return;
        if (res.items.length === 0) {
          setState({ status: 'empty' });
        } else {
          setState({ status: 'ready', items: res.items });
        }
      } catch (err) {
        if (cancelled) return;
        if (isApiErrorStatus(err, 401)) {
          router.push('/login?next=/chat');
          return;
        }
        setState({
          status: 'error',
          message: humanizeError(err, 'chat-load'),
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (state.status === 'loading') {
    return <div className="chat-inbox"><h2>Беседы</h2><span className="auth-hint">Загружаем...</span></div>;
  }
  if (state.status === 'error') {
    return (
      <div className="chat-inbox">
        <h2>Беседы</h2>
        <ErrorAlert message={state.message} />
      </div>
    );
  }
  if (state.status === 'empty') {
    return (
      <div className={compact ? 'chat-inbox' : 'chat-empty'}>
        <h2>{compact ? 'Беседы' : ''}</h2>
        <p>
          У вас пока нет бесед. Откройте страницу компании и нажмите «Связаться», чтобы начать чат.
        </p>
        <Link className="chip" href="/providers?country=RU">Найти компанию →</Link>
      </div>
    );
  }

  return (
    <div className="chat-inbox" aria-label="Список бесед">
      <h2>Беседы</h2>
      {state.items.map((c) => {
        const active = c.id === activeConversationId;
        const title = c.peer?.provider_display_name ?? 'Беседа';
        return (
          <Link
            key={c.id}
            href={`/chat/${c.id}`}
            className={`chat-inbox-item${active ? ' active' : ''}`}
          >
            <strong>{title}</strong>
            <small>{formatTimestamp(c.last_message_at ?? c.updated_at)}</small>
          </Link>
        );
      })}
    </div>
  );
}
