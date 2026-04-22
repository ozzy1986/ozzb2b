'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { ApiError, register } from '@/lib/api';

function toErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 409) return 'Пользователь с таким email уже существует.';
    if (err.status === 422) {
      const detail = err.detail.toLowerCase();
      if (detail.includes('password')) {
        return 'Пароль должен быть не короче 10 символов.';
      }
      if (detail.includes('email')) {
        return 'Проверьте корректность email.';
      }
      return `Проверьте корректность данных: ${err.detail}`;
    }
    return err.detail || 'Не удалось создать аккаунт.';
  }
  return 'Сеть недоступна. Попробуйте ещё раз.';
}

export function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get('next') ?? '/';
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
      setError(toErrorMessage(err));
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
          minLength={10}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <div className="auth-hint">Минимальная длина пароля: 10 символов.</div>
      {error ? <div className="auth-error">{error}</div> : null}
      <button type="submit" disabled={pending}>
        {pending ? 'Создаём...' : 'Зарегистрироваться'}
      </button>
      <div className="auth-hint">
        Уже есть аккаунт? <Link href={`/login?next=${encodeURIComponent(next)}`}>Войти</Link>
      </div>
    </form>
  );
}
