'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import {
  ApiError,
  initiateClaim,
  verifyClaim,
  type ClaimInitiateResponse,
  type ClaimPublic,
} from '@/lib/api';

type Props = {
  providerSlug: string;
  providerDisplayName: string;
  providerWebsite: string | null;
};

type Step = 'intro' | 'instructions' | 'verified';

export function ClaimFlow({ providerSlug, providerDisplayName, providerWebsite }: Props) {
  const router = useRouter();
  const [step, setStep] = useState<Step>('intro');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initiation, setInitiation] = useState<ClaimInitiateResponse | null>(null);
  const [claim, setClaim] = useState<ClaimPublic | null>(null);

  const onStart = useCallback(async () => {
    setError(null);
    setPending(true);
    try {
      const data = await initiateClaim(providerSlug);
      setInitiation(data);
      setStep('instructions');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push(`/login?next=${encodeURIComponent(`/providers/${providerSlug}/claim`)}`);
        return;
      }
      setError(err instanceof ApiError ? err.detail : 'Не удалось начать подтверждение.');
    } finally {
      setPending(false);
    }
  }, [providerSlug, router]);

  const onVerify = useCallback(async () => {
    setError(null);
    setPending(true);
    try {
      const data = await verifyClaim(providerSlug);
      setClaim(data);
      setStep('verified');
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : 'Не удалось проверить meta-тег. Проверьте, что он опубликован на главной странице.',
      );
    } finally {
      setPending(false);
    }
  }, [providerSlug]);

  if (!providerWebsite) {
    return (
      <div className="sidebar-card">
        <p>
          Для подтверждения нужен сайт компании, а он не указан в карточке. Свяжитесь с
          поддержкой: <a href="mailto:hello@ozzb2b.com">hello@ozzb2b.com</a>.
        </p>
      </div>
    );
  }

  if (step === 'intro') {
    return (
      <div className="sidebar-card">
        <h2 style={{ marginTop: 0 }}>Подтверждение владения</h2>
        <p>
          Мы подтверждаем владение компанией «{providerDisplayName}» через публикацию короткого
          meta-тега на главной странице сайта{' '}
          <a href={providerWebsite} target="_blank" rel="noreferrer">
            {providerWebsite.replace(/^https?:\/\//, '')}
          </a>
          .
        </p>
        <ol>
          <li>Нажмите «Начать подтверждение» — мы выдадим уникальный meta-тег.</li>
          <li>Опубликуйте его внутри {'<head>'} главной страницы сайта.</li>
          <li>Нажмите «Проверить» — и получите доступ к редактированию карточки.</li>
        </ol>
        <button type="button" className="contact-cta" onClick={onStart} disabled={pending}>
          {pending ? 'Готовим инструкцию...' : 'Начать подтверждение'}
        </button>
        {error ? <div className="auth-error" style={{ marginTop: 12 }}>{error}</div> : null}
      </div>
    );
  }

  if (step === 'instructions' && initiation) {
    return (
      <div className="sidebar-card">
        <h2 style={{ marginTop: 0 }}>Шаг 2: разместите meta-тег</h2>
        <p>{initiation.instructions}</p>
        <pre
          style={{
            background: '#0f172a',
            color: '#e2e8f0',
            padding: 12,
            borderRadius: 8,
            fontSize: 13,
            overflowX: 'auto',
          }}
        >
          {initiation.meta_tag}
        </pre>
        <p className="auth-hint">
          После публикации нажмите «Проверить». Если не получается — обновите страницу сайта и
          попробуйте ещё раз.
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className="contact-cta" onClick={onVerify} disabled={pending}>
            {pending ? 'Проверяем...' : 'Проверить'}
          </button>
          <button
            type="button"
            className="chip"
            onClick={() => {
              setStep('intro');
              setInitiation(null);
              setError(null);
            }}
            disabled={pending}
          >
            Назад
          </button>
        </div>
        {error ? <div className="auth-error" style={{ marginTop: 12 }}>{error}</div> : null}
      </div>
    );
  }

  if (step === 'verified' && claim) {
    return (
      <div className="sidebar-card">
        <h2 style={{ marginTop: 0 }}>Готово</h2>
        <p>
          Мы подтвердили ваше владение компанией «{providerDisplayName}». Теперь вы можете
          редактировать карточку и получать входящие чаты.
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link className="contact-cta" href="/account/companies">
            Мои компании
          </Link>
          <Link className="chip" href={`/providers/${providerSlug}`}>
            Открыть карточку
          </Link>
        </div>
      </div>
    );
  }

  return null;
}
