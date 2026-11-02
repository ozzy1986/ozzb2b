'use client';

import { useState } from 'react';
import { unsubscribeEmail } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { ErrorAlert } from './ErrorAlert';

// Unsubscribing takes an explicit click: mail scanners pre-fetch links in
// e-mails, and a GET-only flow would silently unsubscribe people.
export function UnsubscribeButton({ email, token }: { email: string; token: string }) {
  const [state, setState] = useState<'idle' | 'pending' | 'done'>('idle');
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setError(null);
    setState('pending');
    try {
      await unsubscribeEmail(email, token);
      setState('done');
    } catch (err) {
      setError(humanizeError(err));
      setState('idle');
    }
  }

  if (state === 'done') {
    return (
      <div className="sidebar-card" role="status">
        Готово: на адрес <strong>{email}</strong> мы больше писать не будем.
      </div>
    );
  }

  return (
    <div className="sidebar-card" style={{ display: 'grid', gap: 12 }}>
      <p>
        Больше не присылать письма на <strong>{email}</strong>?
      </p>
      <div>
        <button
          type="button"
          className="contact-cta"
          onClick={onClick}
          disabled={state === 'pending'}
        >
          {state === 'pending' ? 'Отписываем...' : 'Отписаться'}
        </button>
      </div>
      <ErrorAlert message={error} />
    </div>
  );
}
