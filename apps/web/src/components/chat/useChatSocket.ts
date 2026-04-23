'use client';

import { useEffect, useRef, useState } from 'react';
import { issueWsToken } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import type { ChatMessage } from '@/lib/types';

type State =
  | { status: 'idle' }
  | { status: 'connecting' }
  | { status: 'open' }
  | { status: 'closed' }
  | { status: 'error'; message: string };

type Options = {
  conversationId: string;
  onMessage: (message: ChatMessage) => void;
};

/**
 * Opens a WebSocket connection to the chat gateway for a given conversation.
 *
 * - Asks the API for a short-lived token (re-issued on reconnect).
 * - Reconnects with exponential backoff on transient failures.
 * - Stops and exposes the error on authentication/permission failures.
 */
export function useChatSocket({ conversationId, onMessage }: Options): State {
  const [state, setState] = useState<State>({ status: 'idle' });
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | null = null;
    let retry = 0;

    async function connect() {
      if (cancelled) return;
      try {
        setState({ status: 'connecting' });
        const { ws_url } = await issueWsToken(conversationId);
        if (cancelled) return;
        socket = new WebSocket(ws_url);
        socket.onopen = () => {
          retry = 0;
          setState({ status: 'open' });
        };
        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as ChatMessage;
            onMessageRef.current(data);
          } catch {
            // ignore unparseable frames — they can't be fabricated by us.
          }
        };
        socket.onerror = () => {
          setState({ status: 'error', message: 'Ошибка соединения.' });
        };
        socket.onclose = () => {
          if (cancelled) return;
          setState({ status: 'closed' });
          // Only retry transient closures — the token might simply have
          // expired mid-session.
          const delay = Math.min(10_000, 500 * 2 ** retry);
          retry = Math.min(retry + 1, 5);
          setTimeout(() => {
            if (!cancelled) connect();
          }, delay);
        };
      } catch (err) {
        if (cancelled) return;
        setState({
          status: 'error',
          message: humanizeError(err, 'chat-open'),
        });
      }
    }

    void connect();

    return () => {
      cancelled = true;
      if (socket) {
        socket.onopen = null;
        socket.onmessage = null;
        socket.onerror = null;
        socket.onclose = null;
        try {
          socket.close(1000, 'client closing');
        } catch {
          // ignore
        }
      }
    };
  }, [conversationId]);

  return state;
}
