'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getMe, login as apiLogin, register as apiRegister, logout as apiLogout } from '@/lib/auth-api';
import type { User, LoginCredentials, RegisterCredentials } from '@/types/auth';

interface AuthState {
  user: User | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, isLoading: true });

  useEffect(() => {
    // On mount, restore session via the proxy (which reads the access_token cookie).
    getMe()
      .then((user) => setState({ user, isLoading: false }))
      .catch(() => setState({ user: null, isLoading: false }));
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const { user } = await apiLogin(credentials);
    setState({ user, isLoading: false });
  };

  const register = async (credentials: RegisterCredentials) => {
    const { user } = await apiRegister(credentials);
    setState({ user, isLoading: false });
  };

  const logout = async () => {
    await apiLogout().catch(() => {}); // best-effort
    setState({ user: null, isLoading: false });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
