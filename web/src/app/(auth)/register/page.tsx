'use client';

import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { FormField } from '@/components/forms/FormField';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { getApiErrorMessage } from '@/lib/api-client';

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [fields, setFields] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFields((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await register(fields);
      router.push('/dashboard');
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
          <CardTitle className="text-2xl">Create account</CardTitle>
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
              autoComplete="new-password"
              required
            />
            {error && (
              <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" disabled={submitting} className="mt-1 w-full">
              {submitting ? 'Creating account…' : 'Create account'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center text-sm text-muted-foreground">
          Already have an account?&nbsp;<Link href="/login" className="text-foreground underline">Sign in</Link>
        </CardFooter>
      </Card>
    </main>
  );
}
