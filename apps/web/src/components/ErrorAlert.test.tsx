import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ErrorAlert } from './ErrorAlert';

describe('<ErrorAlert />', () => {
  afterEach(() => cleanup());

  it('renders nothing when message is empty', () => {
    const { container } = render(<ErrorAlert message={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the message with role="alert"', () => {
    render(<ErrorAlert message="Что-то пошло не так" />);
    const alert = screen.getByRole('alert');
    expect(alert.textContent).toContain('Что-то пошло не так');
  });

  it('shows retry button only when onRetry is passed and calls it', () => {
    const onRetry = vi.fn();
    render(<ErrorAlert message="boom" onRetry={onRetry} />);
    const btn = screen.getByRole('button', { name: /повторить/i });
    fireEvent.click(btn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('uses custom retryLabel when provided', () => {
    render(<ErrorAlert message="x" onRetry={() => {}} retryLabel="Обновить" />);
    expect(
      screen.getByRole('button', { name: /обновить/i }),
    ).toBeDefined();
  });

  it('renders an optional action slot', () => {
    render(
      <ErrorAlert
        message="x"
        action={<a href="/help">справка</a>}
      />,
    );
    expect(screen.getByRole('link', { name: /справка/i })).toBeDefined();
  });
});
