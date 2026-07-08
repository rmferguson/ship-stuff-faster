'use client';

import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { FormField } from '@/components/forms/FormField';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { getApiErrorMessage } from '@/lib/api-client';
import { getSafeReturnPath } from '@/lib/url-utils';

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [fields, setFields] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Validate ?next= before using it — prevents open redirect attacks.
  // getSafeReturnPath rejects absolute URLs, protocol-relative paths, and
  // javascript: schemes. Falls back to /dashboard if next is absent or unsafe.
  const redirectTo = getSafeReturnPath(searchParams);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFields((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(fields);
      router.push(redirectTo);
    } catch (err) {
      setError(await getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen bg-muted/40 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Sign in</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <FormField
              label="Email"
              name="email"
              type="email"
              value={fields.email}
              onChange={handleChange}
              autoComplete="email"
              required
            />
            <FormField
              label="Password"
              name="password"
              type="password"
              value={fields.password}
              onChange={handleChange}
              autoComplete="current-password"
              required
            />
            {error && (
              <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" disabled={submitting} className="mt-1 w-full">
              {submitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center text-sm text-muted-foreground">
          Don&apos;t have an account?&nbsp;<Link href="/register" className="text-foreground underline">Register</Link>
        </CardFooter>
      </Card>
    </main>
  );
}
