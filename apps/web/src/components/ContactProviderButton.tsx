'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import { startConversation } from '@/lib/api';
import { humanizeError, isApiErrorStatus } from '@/lib/errors';
import { ErrorAlert } from './ErrorAlert';

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
      if (isApiErrorStatus(err, 401)) {
        router.push(`/login?next=${encodeURIComponent(`/providers/${providerSlug}`)}`);
        return;
      }
      setError(humanizeError(err, 'chat-open'));
    } finally {
      setPending(false);
    }
  }, [providerSlug, router]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <button type="button" className="contact-cta" onClick={onClick} disabled={pending}>
        {pending ? 'Открываем чат...' : 'Связаться'}
      </button>
      <ErrorAlert message={error} onRetry={!pending ? onClick : undefined} />
    </div>
  );
}
