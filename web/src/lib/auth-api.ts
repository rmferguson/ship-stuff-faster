import { api } from './api-client';
import type { LoginCredentials, RegisterCredentials, User } from '@/types/auth';

export interface UserResponse {
  user: User;
}

export function login(credentials: LoginCredentials): Promise<UserResponse> {
  return fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
    credentials: 'include',
  }).then(async (res) => {
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<UserResponse>;
  });
}

export function register(credentials: RegisterCredentials): Promise<UserResponse> {
  return fetch('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
    credentials: 'include',
  }).then(async (res) => {
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<UserResponse>;
  });
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  });
}

export function getMe(): Promise<User> {
  return api.get('auth/me/').json<User>();
}

export async function requestPasswordReset(email: string): Promise<void> {
  await fetch('/api/auth/password-reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
    credentials: 'include',
  });
}

export async function confirmPasswordReset(
  uid: string,
  token: string,
  newPassword: string,
): Promise<void> {
  await fetch('/api/auth/password-reset/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uid, token, new_password: newPassword }),
    credentials: 'include',
  });
}
