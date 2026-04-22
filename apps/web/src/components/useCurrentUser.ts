'use client';

import { useEffect, useState } from 'react';
import { getMe } from '@/lib/api';
import type { UserPublic } from '@/lib/types';

export type CurrentUserState =
  | { status: 'loading' }
  | { status: 'anonymous' }
  | { status: 'authenticated'; user: UserPublic };

/**
 * Client hook that returns the current session user or null.
 * We avoid suspense so caller pages can render a fallback quickly.
 */
export function useCurrentUser(): CurrentUserState {
  const [state, setState] = useState<CurrentUserState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const user = await getMe();
        if (cancelled) return;
        setState(user ? { status: 'authenticated', user } : { status: 'anonymous' });
      } catch {
        if (!cancelled) setState({ status: 'anonymous' });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
