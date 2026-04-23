import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

const push = vi.fn();
const refresh = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push, refresh }),
  useSearchParams: () => new URLSearchParams(),
}));

const login = vi.fn();
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api');
  return { ...actual, login: (...args: unknown[]) => login(...args) };
});

import { ApiError } from '@/lib/api';
import { LoginForm } from './LoginForm';

describe('<LoginForm />', () => {
  afterEach(() => {
    cleanup();
    login.mockReset();
    push.mockReset();
    refresh.mockReset();
  });

  it('submits credentials and navigates on success', async () => {
    login.mockResolvedValue({ access_token: 't' });
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'User@Example.com ' },
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'SuperSecret' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /войти/i }));
    await waitFor(() => expect(login).toHaveBeenCalled());
    expect(login).toHaveBeenCalledWith('user@example.com', 'SuperSecret');
    await waitFor(() => expect(push).toHaveBeenCalledWith('/'));
  });

  it('shows localized error on 401', async () => {
    login.mockRejectedValue(new ApiError(401, 'invalid email or password'));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'x@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'whatever' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /войти/i }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/неверный email или пароль/i);
    expect(push).not.toHaveBeenCalled();
  });

  it('shows network-friendly error on offline', async () => {
    login.mockRejectedValue(new TypeError('Failed to fetch'));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'x@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'whatever' },
    });
    fireEvent.submit(screen.getByRole('button', { name: /войти/i }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toMatch(/нет связи с сервером/i);
  });
});
