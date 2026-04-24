import { describe, expect, it } from 'vitest';
import { safeNextPath } from './safe-next';

describe('safeNextPath', () => {
  it('accepts same-origin absolute paths', () => {
    expect(safeNextPath('/')).toBe('/');
    expect(safeNextPath('/dashboard')).toBe('/dashboard');
    expect(safeNextPath('/providers/acme?tab=info')).toBe(
      '/providers/acme?tab=info',
    );
    expect(safeNextPath('/account/companies/x#section')).toBe(
      '/account/companies/x#section',
    );
  });

  it('rejects protocol-relative URLs (open-redirect classic)', () => {
    expect(safeNextPath('//evil.example')).toBeNull();
    expect(safeNextPath('//evil.example/path')).toBeNull();
  });

  it('rejects backslash-prefixed paths that browsers may normalise', () => {
    expect(safeNextPath('/\\evil.example')).toBeNull();
  });

  it('rejects absolute URLs to other origins', () => {
    expect(safeNextPath('https://evil.example')).toBeNull();
    expect(safeNextPath('http://localhost')).toBeNull();
  });

  it('rejects javascript: and data: schemes', () => {
    expect(safeNextPath('javascript:alert(1)')).toBeNull();
    expect(safeNextPath('data:text/html,<script>alert(1)</script>')).toBeNull();
  });

  it('rejects null, empty and non-string inputs', () => {
    expect(safeNextPath(null)).toBeNull();
    expect(safeNextPath(undefined)).toBeNull();
    expect(safeNextPath('')).toBeNull();
    expect(safeNextPath('  ')).toBeNull();
  });

  it('rejects strings containing control characters', () => {
    expect(safeNextPath('/x\u0000y')).toBeNull();
    expect(safeNextPath('/x\ny')).toBeNull();
  });
});
