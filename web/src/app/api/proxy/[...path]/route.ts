/**
 * GET/POST/PUT/PATCH/DELETE /api/proxy/[...path]
 *
 * Generic Django API proxy. Reads access_token from httpOnly cookie,
 * injects Authorization header, and streams the response back.
 *
 * On 401: tries to refresh using the refresh_token cookie. If refresh
 * succeeds, retries the original request once and updates access_token cookie.
 * If refresh fails, clears both cookies and returns 401.
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { cookies } from 'next/headers';
import {
  getAccessToken,
  getRefreshToken,
  setTokenCookies,
  clearTokenCookies,
} from '@/lib/server/cookies';

const API_BASE = (process.env.API_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '');

interface TokenRefreshResponse {
  access: string;
}

async function refreshAccessToken(refreshToken: string): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (!res.ok) return null;
    const data: TokenRefreshResponse = await res.json();
    return data.access ?? null;
  } catch {
    return null;
  }
}

async function proxyRequest(
  request: NextRequest,
  path: string[],
  accessToken: string,
): Promise<Response> {
  const djangoUrl = `${API_BASE}/${path.join('/')}/`;

  // DELETE is included because DRF accepts an optional body on DELETE requests
  // (e.g. bulk-delete endpoints). Omitting it would silently drop that payload.
  const bodyMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
  const body =
    bodyMethods.has(request.method) ? await request.arrayBuffer().catch(() => undefined) : undefined;

  // Forward relevant headers, excluding host and cookies (auth is via Bearer)
  const forwardHeaders: Record<string, string> = {
    Authorization: `Bearer ${accessToken}`,
  };
  const contentType = request.headers.get('content-type');
  if (contentType) forwardHeaders['Content-Type'] = contentType;
  const accept = request.headers.get('accept');
  if (accept) forwardHeaders['Accept'] = accept;

  return fetch(djangoUrl, {
    method: request.method,
    headers: forwardHeaders,
    body: body !== undefined ? body : undefined,
  });
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return handler(request, await params);
}
export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return handler(request, await params);
}
export async function PUT(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return handler(request, await params);
}
export async function PATCH(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return handler(request, await params);
}
export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  return handler(request, await params);
}

async function handler(
  request: NextRequest,
  params: { path: string[] },
): Promise<NextResponse> {
  const cookieStore = await cookies();
  let accessToken = getAccessToken(cookieStore);

  if (!accessToken) {
    // Try refresh immediately if no access token
    const refreshToken = getRefreshToken(cookieStore);
    if (!refreshToken) {
      return NextResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }
    const newAccess = await refreshAccessToken(refreshToken);
    if (!newAccess) {
      const res = NextResponse.json({ detail: 'Session expired' }, { status: 401 });
      clearTokenCookies(res);
      return res;
    }
    accessToken = newAccess;
  }

  // First attempt
  const djangoRes = await proxyRequest(request, params.path, accessToken).catch(() => null);
  if (!djangoRes) {
    return NextResponse.json({ detail: 'Upstream unavailable' }, { status: 502 });
  }

  if (djangoRes.status !== 401) {
    // Stream response back unchanged
    const body = await djangoRes.arrayBuffer();
    const res = new NextResponse(body, {
      status: djangoRes.status,
      // Fall back to application/json; Django may return text/html on unhandled errors.
      headers: { 'Content-Type': djangoRes.headers.get('content-type') ?? 'application/json' },
    });
    return res;
  }

  // 401 — attempt token refresh
  const refreshToken = getRefreshToken(cookieStore);
  if (!refreshToken) {
    const res = NextResponse.json({ detail: 'Session expired' }, { status: 401 });
    clearTokenCookies(res);
    return res;
  }

  const newAccess = await refreshAccessToken(refreshToken);
  if (!newAccess) {
    const res = NextResponse.json({ detail: 'Session expired' }, { status: 401 });
    clearTokenCookies(res);
    return res;
  }

  // Retry original request with new access token
  const retryRes = await proxyRequest(request, params.path, newAccess).catch(() => null);
  if (!retryRes) {
    return NextResponse.json({ detail: 'Upstream unavailable after refresh' }, { status: 502 });
  }

  const retryBody = await retryRes.arrayBuffer();
  const finalRes = new NextResponse(retryBody, {
    status: retryRes.status,
    headers: { 'Content-Type': retryRes.headers.get('content-type') ?? 'application/json' },
  });
  // Update access_token cookie with fresh value
  setTokenCookies(finalRes, newAccess);
  return finalRes;
}
