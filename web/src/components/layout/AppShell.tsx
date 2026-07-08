'use client';

import { useAuth } from '@/hooks/useAuth';

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex flex-col min-h-screen">
      <nav className="sticky top-0 z-10 flex items-center justify-between px-6 h-14 border-b bg-background">
        <span className="font-semibold text-lg">App</span>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">{user?.email}</span>
          <button
            onClick={logout}
            className="text-sm px-2 py-1 rounded hover:bg-accent transition-colors"
          >
            Sign out
          </button>
        </div>
      </nav>
      <div className="flex flex-1">
        <aside className="hidden md:block w-56 shrink-0 border-r py-4" />
        <main className="flex-1 p-8 min-w-0">{children}</main>
      </div>
    </div>
  );
}
