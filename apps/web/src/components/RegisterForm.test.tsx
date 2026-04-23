import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

const push = vi.fn();
const refresh = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push, refresh }),
  useSearchParams: () => new URLSearchParams(),
}));

const registerApi = vi.fn();
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api');
  return { ...actual, register: (...args: unknown[]) => registerApi(...args) };
});

import { ApiError } from '@/lib/api';
import { RegisterForm } from './RegisterForm';

describe('<RegisterForm />', () => {
  afterEach(() => {
    cleanup();
    registerApi.mockReset();
    push.mockReset();
    refresh.mockReset();
  });

  it('normalises email and forwards all fields on submit', async () => {
    registerApi.mockResolvedValue({ access_token: 't' });
    render(<RegisterForm />);
    fireEvent.change(screen.getByLabelText(/имя/i), {
      target: { value: '  Алексей  ' },
    });
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: ' New@Example.com ' },
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'SuperSecret!' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /зарегистрироваться/i }));
    await waitFor(() => expect(registerApi).toHaveBeenCalled());
    expect(registerApi).toHaveBeenCalledWith(
      'new@example.com',
      'SuperSecret!',
      'Алексей',
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith('/'));
  });

  it('shows localized error when the email is already taken', async () => {
    registerApi.mockRejectedValue(new ApiError(409, 'email already registered'));
    render(<RegisterForm />);
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'dup@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'SuperSecret!' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /зарегистрироваться/i }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/уже зарегистрирован/i);
    expect(push).not.toHaveBeenCalled();
  });

  it('sends empty display name as null', async () => {
    registerApi.mockResolvedValue({ access_token: 't' });
    render(<RegisterForm />);
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'a@b.com' },
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'SuperSecret!' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /зарегистрироваться/i }));
    await waitFor(() =>
      expect(registerApi).toHaveBeenCalledWith('a@b.com', 'SuperSecret!', null),
    );
  });
});
