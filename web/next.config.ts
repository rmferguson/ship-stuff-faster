import type { NextConfig } from 'next';

/**
 * Content Security Policy headers.
 *
 * Enforced (not report-only) — XSS is blocked, not just reported.
 *
 * Directives:
 * - default-src 'self': Allow resources only from this origin by default.
 * - script-src 'self': No inline scripts. Next.js uses server-side nonce for
 *   its own scripts in production; add a nonce header if you enable PPR/ISR.
 * - style-src 'self' 'unsafe-inline': Tailwind injects styles at build time;
 *   unsafe-inline is required unless you adopt CSS Modules or hash-based CSP.
 * - img-src 'self' data: blob:: Allow self-hosted images, data URIs (icons),
 *   and blob URIs (canvas previews).
 * - font-src 'self': Block third-party font CDNs. Host fonts locally.
 * - connect-src 'self': Fetch/XHR only to this origin. Add your API origin
 *   when deploying separately (e.g. 'self' https://api.yourdomain.com).
 * - frame-ancestors 'none': Deny embedding in iframes — prevents clickjacking.
 * - form-action 'self': Forms may only submit to this origin.
 * - base-uri 'self': Prevent base tag injection attacks.
 * - object-src 'none': Disable Flash and other plugin content.
 * - upgrade-insecure-requests: Upgrade HTTP requests to HTTPS automatically.
 *
 * To relax a directive for a specific third-party (e.g. analytics):
 *   Add the origin to the relevant directive (script-src, connect-src, etc.)
 *   Never add 'unsafe-eval' or 'unsafe-inline' to script-src.
 */
const cspDirectives = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  'upgrade-insecure-requests',
].join('; ');

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: cspDirectives,
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
