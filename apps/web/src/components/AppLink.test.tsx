import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import AppLink from './AppLink';

describe('<AppLink />', () => {
  afterEach(() => cleanup());

  it('renders a native anchor for internal routes', () => {
    render(<AppLink href="/providers?country=RU">Providers</AppLink>);

    const link = screen.getByRole('link', { name: 'Providers' });
    expect(link.tagName).toBe('A');
    expect(link.getAttribute('href')).toBe('/providers?country=RU');
  });

  it('stringifies object href values', () => {
    render(
      <AppLink href={{ pathname: '/providers', query: { country: 'RU' } }}>
        Providers
      </AppLink>,
    );

    expect(screen.getByRole('link').getAttribute('href')).toBe('/providers?country=RU');
  });
});
