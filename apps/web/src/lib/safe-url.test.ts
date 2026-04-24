import { describe, expect, it } from 'vitest';
import { safeUrl } from './safe-url';

describe('safeUrl', () => {
  it('passes through https:// URLs', () => {
    expect(safeUrl('https://example.com')).toBe('https://example.com/');
    expect(safeUrl('https://example.com/path?x=1')).toBe(
      'https://example.com/path?x=1',
    );
  });

  it('passes through http:// URLs (kept for legacy directory entries)', () => {
    expect(safeUrl('http://example.com')).toBe('http://example.com/');
  });

  it('upgrades a bare host to https://', () => {
    expect(safeUrl('example.com')).toBe('https://example.com/');
    expect(safeUrl('example.com/path')).toBe('https://example.com/path');
  });

  it('passes through mailto: and tel: with valid payloads', () => {
    expect(safeUrl('mailto:hello@example.com')).toBe('mailto:hello@example.com');
    expect(safeUrl('tel:+74951234567')).toBe('tel:+74951234567');
  });

  it('rejects javascript:, data:, vbscript: schemes', () => {
    expect(safeUrl('javascript:alert(1)')).toBeNull();
    expect(safeUrl('JAVASCRIPT:alert(1)')).toBeNull();
    expect(safeUrl('data:text/html,<script>')).toBeNull();
    expect(safeUrl('vbscript:msgbox')).toBeNull();
  });

  it('rejects null/undefined/empty inputs', () => {
    expect(safeUrl(null)).toBeNull();
    expect(safeUrl(undefined)).toBeNull();
    expect(safeUrl('')).toBeNull();
    expect(safeUrl('   ')).toBeNull();
  });

  it('rejects malformed URLs', () => {
    expect(safeUrl('http://')).toBeNull();
  });
});
