'use client';

import type { CSSProperties, ReactNode } from 'react';

type Props = {
  /** Error message to display. When empty/null the component renders nothing. */
  message: string | null | undefined;
  /** Optional retry handler. When provided, a "Повторить" button is shown. */
  onRetry?: () => void;
  /** Override the default retry button label. */
  retryLabel?: string;
  /** Optional slot for extra actions (e.g. a link). */
  action?: ReactNode;
  className?: string;
  style?: CSSProperties;
};

/**
 * Unified, accessible error banner.
 *
 * Uses role="alert" so screen readers announce changes immediately.
 * Visual treatment lives in globals.css under `.error-alert`.
 */
export function ErrorAlert({
  message,
  onRetry,
  retryLabel = 'Повторить',
  action,
  className,
  style,
}: Props) {
  if (!message) return null;
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`error-alert${className ? ` ${className}` : ''}`}
      style={style}
    >
      <span className="error-alert-icon" aria-hidden="true">
        ⚠
      </span>
      <span className="error-alert-text">{message}</span>
      {onRetry ? (
        <button
          type="button"
          className="error-alert-retry"
          onClick={onRetry}
        >
          {retryLabel}
        </button>
      ) : null}
      {action ? <span className="error-alert-action">{action}</span> : null}
    </div>
  );
}
