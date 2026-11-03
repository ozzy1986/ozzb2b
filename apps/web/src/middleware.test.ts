import { describe, expect, it } from 'vitest';
import { NextRequest } from 'next/server';
import { middleware } from '../middleware';

function run(url: string, headers: Record<string, string>) {
  return middleware(new NextRequest(url, { headers }));
}

describe('canonical host redirect', () => {
  it('leaves https://ozzb2b.com alone', () => {
    const res = run('http://127.0.0.1:3000/providers', {
      host: 'ozzb2b.com',
      'x-forwarded-proto': 'https',
    });
    expect(res.headers.get('location')).toBeNull();
  });

  it('sends http to https with path and query', () => {
    const res = run('http://127.0.0.1:3000/providers?category=it', {
      host: 'ozzb2b.com',
      'x-forwarded-proto': 'http',
    });
    expect(res.status).toBe(301);
    expect(res.headers.get('location')).toBe('https://ozzb2b.com/providers?category=it');
  });

  it('drops www', () => {
    const res = run('http://127.0.0.1:3000/request', {
      host: 'www.ozzb2b.com',
      'x-forwarded-proto': 'https',
    });
    expect(res.status).toBe(301);
    expect(res.headers.get('location')).toBe('https://ozzb2b.com/request');
  });

  it('ignores other hosts', () => {
    const res = run('http://localhost:3000/', { host: 'localhost:3000' });
    expect(res.headers.get('location')).toBeNull();
  });
});
