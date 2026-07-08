/**
 * Server-side cookie helpers for auth token management.
 *
 * Auth cookies use path=/api/ so they are only sent on requests to Next.js
 * API routes — never to page routes. This minimises the cookie's attack surface.
 */
import { NextResponse } from 'next/server';
import type { ResponseCookie } from 'next/dist/compiled/@edge-runtime/cookies';
import type { ReadonlyRequestCookies } from 'next/dist/server/web/spec-extension/adapters/request-cookies';

const ACCESS_TOKEN = 'access_token';
const REFRESH_TOKEN = 'refresh_token';

function authCookieOptions(overrides?: Partial<ResponseCookie>): ResponseCookie {
  return {
    name: '',
    value: '',
    httpOnly: true,
    path: '/api/',
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    ...overrides,
  };
}

export function setTokenCookies(
  res: NextResponse,
  access: string,
  refresh?: string,
): void {
  res.cookies.set({
    ...authCookieOptions(),
    name: ACCESS_TOKEN,
    value: access,
  });
  if (refresh !== undefined) {
    res.cookies.set({
      ...authCookieOptions(),
      name: REFRESH_TOKEN,
      value: refresh,
    });
  }
}

export function clearTokenCookies(res: NextResponse): void {
  res.cookies.set({
    ...authCookieOptions({ maxAge: 0 }),
    name: ACCESS_TOKEN,
    value: '',
  });
  res.cookies.set({
    ...authCookieOptions({ maxAge: 0 }),
    name: REFRESH_TOKEN,
    value: '',
  });
}

export function getAccessToken(cookieStore: ReadonlyRequestCookies): string | undefined {
  return cookieStore.get(ACCESS_TOKEN)?.value;
}

export function getRefreshToken(cookieStore: ReadonlyRequestCookies): string | undefined {
  return cookieStore.get(REFRESH_TOKEN)?.value;
}
