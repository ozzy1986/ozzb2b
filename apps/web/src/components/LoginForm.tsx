'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { ApiError, login } from '@/lib/api';

function toErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return 'Неверный email или пароль.';
    return err.detail || 'Не удалось войти.';
  }
  return 'Сеть недоступна. Попробуйте ещё раз.';
}

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
      setError(toErrorMessage(err));
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
      {error ? <div className="auth-error">{error}</div> : null}
      <button type="submit" disabled={pending}>
        {pending ? 'Входим...' : 'Войти'}
      </button>
      <div className="auth-hint">
        Нет аккаунта? <Link href={`/register?next=${encodeURIComponent(next)}`}>Зарегистрироваться</Link>
      </div>
    </form>
  );
}
