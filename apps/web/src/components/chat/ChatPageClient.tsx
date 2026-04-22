'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ApiError,
  getConversation,
  listMessages,
  sendMessage,
} from '@/lib/api';
import type { ChatMessage, Conversation } from '@/lib/types';
import { ChatInbox } from './ChatInbox';
import { useChatSocket } from './useChatSocket';
import { useCurrentUser } from '../useCurrentUser';

type Props = {
  conversationId: string;
};

type MessagesState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; items: ChatMessage[] };

function formatTime(iso: string): string {
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

function mergeMessage(items: ChatMessage[], incoming: ChatMessage): ChatMessage[] {
  if (items.some((m) => m.id === incoming.id)) return items;
  return [...items, incoming].sort((a, b) => a.created_at.localeCompare(b.created_at));
}

export function ChatPageClient({ conversationId }: Props) {
  const router = useRouter();
  const me = useCurrentUser();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<MessagesState>({ status: 'loading' });
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [conv, msgs] = await Promise.all([
          getConversation(conversationId),
          listMessages(conversationId, { limit: 200 }),
        ]);
        if (cancelled) return;
        setConversation(conv);
        setMessages({ status: 'ready', items: msgs.items });
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          router.push(`/login?next=/chat/${conversationId}`);
          return;
        }
        if (err instanceof ApiError && err.status === 403) {
          router.push('/chat');
          return;
        }
        setMessages({
          status: 'error',
          message: err instanceof Error ? err.message : 'Не удалось загрузить беседу.',
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId, router]);

  const handleIncoming = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
      if (prev.status !== 'ready') return prev;
      return { status: 'ready', items: mergeMessage(prev.items, msg) };
    });
  }, []);
  const socket = useChatSocket({ conversationId, onMessage: handleIncoming });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const myId = me.status === 'authenticated' ? me.user.id : null;
  const peerName = conversation?.peer?.provider_display_name ?? 'Беседа';

  const onSend = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const body = draft.trim();
      if (!body) return;
      setSending(true);
      setSendError(null);
      try {
        const msg = await sendMessage(conversationId, body);
        setMessages((prev) => {
          if (prev.status !== 'ready') return prev;
          return { status: 'ready', items: mergeMessage(prev.items, msg) };
        });
        setDraft('');
      } catch (err) {
        setSendError(
          err instanceof ApiError ? err.detail : 'Не удалось отправить. Попробуйте ещё раз.',
        );
      } finally {
        setSending(false);
      }
    },
    [conversationId, draft],
  );

  const connectionLabel = useMemo(() => {
    switch (socket.status) {
      case 'connecting':
        return '🟡 подключаемся';
      case 'open':
        return '🟢 онлайн';
      case 'closed':
        return '⚪️ переподключение';
      case 'error':
        return `🔴 ${socket.message}`;
      default:
        return '';
    }
  }, [socket]);

  return (
    <div className="chat-layout">
      <ChatInbox activeConversationId={conversationId} compact />
      <section className="chat-panel">
        <div className="chat-header">
          <div>
            <h2>{peerName}</h2>
            {conversation?.peer ? (
              <Link href={`/providers/${conversation.peer.provider_slug}`} className="auth-hint">
                Открыть профиль компании →
              </Link>
            ) : null}
          </div>
          <div className="auth-hint" aria-live="polite">
            {connectionLabel}
          </div>
        </div>

        <div className="chat-messages">
          {messages.status === 'loading' ? (
            <div className="auth-hint">Загружаем сообщения...</div>
          ) : messages.status === 'error' ? (
            <div className="auth-error">{messages.message}</div>
          ) : messages.items.length === 0 ? (
            <div className="auth-hint">
              Пока нет сообщений. Напишите первым — это безопасно и бесплатно.
            </div>
          ) : (
            messages.items.map((m) => (
              <div
                key={m.id}
                className={`chat-msg${m.sender_user_id === myId ? ' mine' : ''}`}
              >
                {m.body}
                <time dateTime={m.created_at}>{formatTime(m.created_at)}</time>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-form" onSubmit={onSend}>
          <textarea
            name="body"
            required
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Напишите сообщение..."
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
            disabled={sending}
          />
          <button type="submit" disabled={sending || draft.trim().length === 0}>
            {sending ? 'Отправка...' : 'Отправить'}
          </button>
        </form>
        {sendError ? <div className="auth-error" style={{ padding: 8 }}>{sendError}</div> : null}
      </section>
    </div>
  );
}
