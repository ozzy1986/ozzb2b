'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import { ApiError, startConversation } from '@/lib/api';

type Props = {
  providerSlug: string;
};

export function ContactProviderButton({ providerSlug }: Props) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onClick = useCallback(async () => {
    setError(null);
    setPending(true);
    try {
      const conv = await startConversation(providerSlug);
      router.push(`/chat/${conv.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push(`/login?next=${encodeURIComponent(`/providers/${providerSlug}`)}`);
        return;
      }
      setError(
        err instanceof ApiError ? err.detail : 'Не удалось открыть чат. Попробуйте ещё раз.',
      );
    } finally {
      setPending(false);
    }
  }, [providerSlug, router]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <button type="button" className="contact-cta" onClick={onClick} disabled={pending}>
        {pending ? 'Открываем чат...' : 'Связаться'}
      </button>
      {error ? <div className="auth-error">{error}</div> : null}
    </div>
  );
}
