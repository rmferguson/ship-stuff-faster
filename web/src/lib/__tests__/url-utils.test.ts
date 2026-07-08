/**
 * Tests for isSafeReturnPath and getSafeReturnPath.
 *
 * isSafeReturnPath is a security boundary — it must reject all forms of open
 * redirect (javascript:, //evil.com, absolute URLs, etc.). Test coverage here
 * is not optional: a missed case is a security vulnerability.
 */
import { describe, expect, it } from 'vitest';
import { getSafeReturnPath, isSafeReturnPath } from '../url-utils';

describe('isSafeReturnPath', () => {
  describe('valid paths (should return true)', () => {
    it('accepts simple relative path', () => {
      expect(isSafeReturnPath('/dashboard')).toBe(true);
    });

    it('accepts root path', () => {
      expect(isSafeReturnPath('/')).toBe(true);
    });

    it('accepts nested path', () => {
      expect(isSafeReturnPath('/items/123/edit')).toBe(true);
    });

    it('accepts path with query string', () => {
      expect(isSafeReturnPath('/search?q=hello')).toBe(true);
    });

    it('accepts path with hash', () => {
      expect(isSafeReturnPath('/docs#section-1')).toBe(true);
    });
  });

  describe('invalid paths (should return false)', () => {
    it('rejects null', () => {
      expect(isSafeReturnPath(null)).toBe(false);
    });

    it('rejects undefined', () => {
      expect(isSafeReturnPath(undefined)).toBe(false);
    });

    it('rejects empty string', () => {
      expect(isSafeReturnPath('')).toBe(false);
    });

    it('rejects absolute URL with http', () => {
      expect(isSafeReturnPath('http://evil.com/phish')).toBe(false);
    });

    it('rejects absolute URL with https', () => {
      expect(isSafeReturnPath('https://evil.com/phish')).toBe(false);
    });

    it('rejects protocol-relative URL', () => {
      // //evil.com — browser treats this as https://evil.com
      expect(isSafeReturnPath('//evil.com/phish')).toBe(false);
    });

    it('rejects javascript: scheme', () => {
      expect(isSafeReturnPath('javascript:alert(1)')).toBe(false);
    });

    it('rejects data: scheme', () => {
      expect(isSafeReturnPath('data:text/html,<script>alert(1)</script>')).toBe(false);
    });

    it('rejects path with @ sign (user@host trick)', () => {
      // //user@evil.com — browser sees evil.com as host
      expect(isSafeReturnPath('/user@evil.com')).toBe(false);
    });

    it('rejects path-relative URL (no leading slash)', () => {
      expect(isSafeReturnPath('evil.com/phish')).toBe(false);
    });

    it('rejects null byte in path', () => {
      expect(isSafeReturnPath('/path\x00evil')).toBe(false);
    });

    it('rejects newline in path (header injection)', () => {
      expect(isSafeReturnPath('/path\nevil')).toBe(false);
    });

    it('rejects carriage return in path', () => {
      expect(isSafeReturnPath('/path\revil')).toBe(false);
    });
  });
});

describe('getSafeReturnPath', () => {
  it('returns validated next param when safe', () => {
    const params = new URLSearchParams('next=/dashboard');
    expect(getSafeReturnPath(params)).toBe('/dashboard');
  });

  it('returns fallback when next is absent', () => {
    const params = new URLSearchParams();
    expect(getSafeReturnPath(params)).toBe('/dashboard');
  });

  it('returns fallback when next is unsafe', () => {
    const params = new URLSearchParams('next=//evil.com');
    expect(getSafeReturnPath(params)).toBe('/dashboard');
  });

  it('returns fallback when next is javascript:', () => {
    const params = new URLSearchParams('next=javascript:alert(1)');
    expect(getSafeReturnPath(params)).toBe('/dashboard');
  });

  it('returns custom fallback', () => {
    const params = new URLSearchParams('next=//evil.com');
    expect(getSafeReturnPath(params, '/home')).toBe('/home');
  });

  it('handles null searchParams', () => {
    expect(getSafeReturnPath(null)).toBe('/dashboard');
  });
});
