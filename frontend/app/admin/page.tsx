'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Logomark from '../components/Logomark';
import SubmissionsTab from './components/SubmissionsTab';
import QueriesTab from './components/QueriesTab';
import StatsTab from './components/StatsTab';

export default function AdminPage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [authed, setAuthed] = useState(false);
  const [tab, setTab] = useState<'submissions' | 'queries' | 'stats'>('submissions');

  // Bumping this is how the header's "Refresh" button tells whichever
  // tab is currently mounted to re-fetch, without the parent needing to
  // know how each tab fetches its own data.
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const t = sessionStorage.getItem('autovalu_token');
    if (!t) { router.push('/admin/login'); return; }
    setToken(t);
    setAuthed(true);
  }, [router]);

  const logout = () => {
    sessionStorage.removeItem('autovalu_token');
    router.push('/admin/login');
  };

  if (!authed) return null;

  return (
    <div className="min-h-screen bg-paper text-ink-950">
      {/* HEADER */}
      <div className="flex items-center gap-3 bg-steel px-8 py-4">
        <Logomark className="h-6 w-6 text-amber" />
        <div>
          <div className="font-display text-base font-bold uppercase tracking-tight text-paper">
            Auto<span className="text-amber">Valu</span> Admin
          </div>
          <div className="text-xs text-surface-alt">Price Intelligence Dashboard</div>
        </div>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="ml-auto rounded bg-amber px-4 py-1.5 text-xs font-bold text-steel transition-colors hover:bg-amber-hover hover:text-paper"
        >
          ↻ Refresh
        </button>
        <button
          onClick={logout}
          className="rounded border border-white/15 px-3.5 py-1.5 text-xs font-bold text-surface-alt transition-colors hover:border-white/30 hover:text-paper"
        >
          Sign out
        </button>
      </div>

      {/* TABS */}
      <div className="flex border-b border-border bg-surface px-8">
        {(['submissions', 'queries', 'stats'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`border-b-2 px-4 py-3 text-sm font-medium capitalize transition-colors ${
              tab === t ? 'border-amber text-ink-950' : 'border-transparent text-ink-500 hover:text-ink-950'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="px-8 py-6">
        {tab === 'submissions' && <SubmissionsTab token={token} refreshKey={refreshKey} />}
        {tab === 'queries' && <QueriesTab token={token} refreshKey={refreshKey} />}
        {tab === 'stats' && <StatsTab token={token} refreshKey={refreshKey} />}
      </div>
    </div>
  );
}