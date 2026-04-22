import type { Metadata } from 'next';
import { Suspense } from 'react';
import { LoginForm } from '@/components/LoginForm';

export const metadata: Metadata = {
  title: 'Вход',
  description: 'Вход в аккаунт ozzb2b.',
};

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="auth-form"><h1>Вход</h1></div>}>
      <LoginForm />
    </Suspense>
  );
}
