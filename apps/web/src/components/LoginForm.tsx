'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { login } from '@/lib/api';
import { humanizeError } from '@/lib/errors';
import { ErrorAlert } from './ErrorAlert';

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get('next') ?? '/';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await login(email.trim().toLowerCase(), password);
      router.push(next);
      router.refresh();
    } catch (err) {
      setError(humanizeError(err, 'auth-login'));
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={onSubmit} noValidate>
      <h1>Вход</h1>
      <label>
        Email
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
          minLength={8}
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <ErrorAlert message={error} />
      <button type="submit" disabled={pending}>
        {pending ? 'Входим...' : 'Войти'}
      </button>
      <div className="auth-hint">
        Нет аккаунта? <Link href={`/register?next=${encodeURIComponent(next)}`}>Зарегистрироваться</Link>
      </div>
    </form>
  );
}
