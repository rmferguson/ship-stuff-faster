/**
 * POST /api/auth/signup
 *
 * Same httpOnly-cookie proxy pattern as /api/auth/login.
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { setTokenCookies } from '@/lib/server/cookies';

const API_BASE = (process.env.API_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '');

interface DjangoAuthResponse {
  user: { id: number; email: string };
  access: string;
}

function extractRefreshFromSetCookie(header: string): string | undefined {
  const match = header.match(/refresh_token=([^;]+)/);
  return match?.[1];
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (!body) {
    return NextResponse.json({ detail: 'Invalid request body' }, { status: 400 });
  }

  const djangoRes = await fetch(`${API_BASE}/auth/signup/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).catch(() => null);

  if (!djangoRes) {
    return NextResponse.json({ detail: 'Upstream unavailable' }, { status: 502 });
  }

  if (!djangoRes.ok) {
    const errorBody = await djangoRes.text();
    return new NextResponse(errorBody, {
      status: djangoRes.status,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const data: DjangoAuthResponse = await djangoRes.json();
  const setCookieHeader = djangoRes.headers.get('set-cookie') ?? '';
  const refreshValue = extractRefreshFromSetCookie(setCookieHeader);

  const res = NextResponse.json({ user: data.user });
  setTokenCookies(res, data.access, refreshValue);
  return res;
}
