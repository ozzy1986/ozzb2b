'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { register } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { safeNextPath } from '@/lib/safe-next';
import { ErrorAlert } from './ErrorAlert';

export function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  // Sanitize `?next=` so it can never trigger an open redirect to a foreign
  // origin (e.g. `?next=//evil.example` or `?next=https://evil.example`).
  const next = safeNextPath(params.get('next')) ?? '/';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await register(
        email.trim().toLowerCase(),
        password,
        displayName.trim() || null,
      );
      router.push(next);
      router.refresh();
    } catch (err) {
      setError(humanizeError(err, 'auth-register'));
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={onSubmit} noValidate>
      <h1>Регистрация</h1>
      <label>
        Имя
        <input
          type="text"
          name="displayName"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Как к вам обращаться"
        />
      </label>
      <label>
        Электронная почта
        <input
          type="email"
          name="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </label>
      <label>
        Пароль
        <input
          type="password"
          name="password"
          required
          minLength={10}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <div className="auth-hint">Минимальная длина пароля: 10 символов.</div>
      <ErrorAlert message={error} />
      <button type="submit" disabled={pending}>
        {pending ? 'Создаём...' : 'Зарегистрироваться'}
      </button>
      <div className="auth-hint">
        Уже есть аккаунт? <Link href={`/login?next=${encodeURIComponent(next)}`}>Войти</Link>
      </div>
    </form>
  );
}
