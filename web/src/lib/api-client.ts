/**
 * API client — thin ky wrapper.
 *
 * Auth is now handled by Next.js server-side proxy routes at /api/proxy/*.
 * The browser never sees raw JWT values; tokens live in httpOnly cookies.
 * Retry-on-401 logic lives in the proxy (/api/proxy/[...path]/route.ts).
 *
 * Use credentials: 'include' so the browser sends auth cookies on every
 * request to the proxy routes.
 */

import ky, { HTTPError } from 'ky';

export const api = ky.create({
  prefixUrl: '/api/proxy/',
  credentials: 'include',
});

/** Extract a human-readable message from a DRF error response. */
export async function getApiErrorMessage(err: unknown): Promise<string> {
  if (err instanceof HTTPError) {
    try {
      const data = (await err.response.json()) as Record<string, unknown>;
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.non_field_errors)) return (data.non_field_errors as string[]).join(' ');
      const messages = Object.values(data).flat().filter((v) => typeof v === 'string') as string[];
      if (messages.length) return messages.join(' ');
    } catch {}
  }
  return 'Something went wrong. Please try again.';
}
