import type { Metadata } from 'next';
import { Suspense } from 'react';
import { RegisterForm } from '@/components/RegisterForm';

export const metadata: Metadata = {
  title: 'Регистрация',
  description: 'Создать аккаунт ozzb2b.',
};

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="auth-form"><h1>Регистрация</h1></div>}>
      <RegisterForm />
    </Suspense>
  );
}
