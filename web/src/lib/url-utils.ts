/**
 * URL validation utilities for safe redirects.
 *
 * The ?next= redirect pattern (send users back where they came from after login)
 * is an open redirect vulnerability if not validated. `isSafeReturnPath` ensures
 * the redirect target stays within this application.
 *
 * Security rules enforced:
 * 1. Must be a relative path (starts with /)
 * 2. Must not be protocol-relative (not //)
 * 3. Must not contain javascript:, data:, or other dangerous protocols
 * 4. Must not contain @-signs (used in //user@attacker.com tricks)
 * 5. Must be a valid URL path segment (no embedded newlines, null bytes, etc.)
 *
 * Usage:
 *   const next = searchParams.get('next');
 *   const redirect = isSafeReturnPath(next) ? next : '/dashboard';
 *   router.push(redirect);
 */

/**
 * Returns true if `path` is a safe same-origin return path.
 *
 * A safe return path:
 * - Is a non-empty string
 * - Starts with exactly one /
 * - Does not start with // (protocol-relative)
 * - Does not contain : before the first / (no scheme like javascript:)
 * - Does not contain @ (open redirect via user@host form)
 * - Does not contain control characters (newlines, null bytes)
 *
 * @example
 * isSafeReturnPath('/dashboard')     // true
 * isSafeReturnPath('/items/123')     // true
 * isSafeReturnPath('/')              // true
 * isSafeReturnPath('//evil.com')     // false — protocol-relative
 * isSafeReturnPath('javascript:..') // false — JS protocol
 * isSafeReturnPath('http://...')     // false — absolute URL
 * isSafeReturnPath(null)             // false — null
 * isSafeReturnPath('')              // false — empty
 */
export function isSafeReturnPath(path: string | null | undefined): path is string {
  if (!path || typeof path !== 'string') return false;

  // Must start with exactly one slash (relative path)
  if (!path.startsWith('/')) return false;

  // Must not start with // (protocol-relative — attacker can set //evil.com)
  if (path.startsWith('//')) return false;

  // Must not contain @ (open redirect via //@evil.com or //user@evil.com)
  if (path.includes('@')) return false;

  // Must not contain a colon before the first slash separator
  // Guards against: javascript:alert(1), data:text/html,...
  const colonIndex = path.indexOf(':');
  if (colonIndex !== -1) {
    const firstSlashAfterStart = path.indexOf('/', 1);
    if (firstSlashAfterStart === -1 || colonIndex < firstSlashAfterStart) return false;
  }

  // Must not contain control characters (null bytes, newlines, carriage returns)
  if (/[\x00-\x1f\x7f]/.test(path)) return false;

  return true;
}

/**
 * Extract the ?next= parameter from URL search params and validate it.
 *
 * Returns the validated path, or `fallback` (default: '/dashboard') if the
 * next param is absent or unsafe.
 *
 * @example
 * // In a login page:
 * const searchParams = useSearchParams();
 * const redirectTo = getSafeReturnPath(searchParams, '/dashboard');
 * router.push(redirectTo);
 */
export function getSafeReturnPath(
  searchParams: URLSearchParams | null,
  fallback = '/dashboard',
): string {
  const next = searchParams?.get('next');
  return isSafeReturnPath(next) ? next : fallback;
}
