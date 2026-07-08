import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Dashboard' };

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <p>You&apos;re in. Build something.</p>
    </div>
  );
}
