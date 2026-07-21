import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import AppLink from './AppLink';

describe('<AppLink />', () => {
  afterEach(() => cleanup());

  it('renders a native anchor for internal routes', () => {
    render(<AppLink href="/providers?country=RU">Компании</AppLink>);

    const link = screen.getByRole('link', { name: 'Компании' });
    expect(link.tagName).toBe('A');
    expect(link.getAttribute('href')).toBe('/providers?country=RU');
  });

  it('stringifies object href values', () => {
    render(
      <AppLink href={{ pathname: '/providers', query: { country: 'RU' } }}>
        Компании
      </AppLink>,
    );

    expect(screen.getByRole('link').getAttribute('href')).toBe('/providers?country=RU');
  });
});
