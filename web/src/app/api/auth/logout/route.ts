/**
 * POST /api/auth/logout
 *
 * Calls Django logout (best-effort), then clears auth httpOnly cookies
 * regardless of whether Django's call succeeded.
 */
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { clearTokenCookies, getAccessToken } from '@/lib/server/cookies';

const API_BASE = (process.env.API_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '');

export async function POST() {
  const cookieStore = await cookies();
  const accessToken = getAccessToken(cookieStore);

  // Best-effort: call Django logout. Do not fail if it errors.
  if (accessToken) {
    await fetch(`${API_BASE}/auth/logout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
    }).catch(() => {});
  }

  const res = new NextResponse(null, { status: 204 });
  clearTokenCookies(res);
  return res;
}
