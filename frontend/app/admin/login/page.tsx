'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Logomark from '../../components/Logomark';

const ML_API = process.env.NEXT_PUBLIC_ML_URL ?? 'http://localhost:8000';

export default function AdminLogin() {
  const [form,    setForm]    = useState({ username:'', password:'' });
  const [error,   setError]   = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res  = await fetch(`${ML_API}/admin/login`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(form),
      });
      if (!res.ok) { setError('Invalid username or password.'); setLoading(false); return; }
      const data = await res.json();
      sessionStorage.setItem('autovalu_token', data.token);
      router.push('/admin');
    } catch {
      setError('Cannot connect to server.');
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6">
      <div className="w-full max-w-sm rounded-md border border-border bg-surface p-9">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-md bg-steel">
            <Logomark className="h-6 w-6 text-amber" />
          </div>
          <div className="font-display text-xl font-bold uppercase tracking-tight text-ink-950">
            Auto<span className="text-amber">Valu</span> Admin
          </div>
          <div className="mt-1 text-sm text-ink-500">Sign in to access the dashboard</div>
        </div>

        <form onSubmit={submit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium uppercase tracking-wide text-ink-500">Username</label>
            <input
              type="text" value={form.username} required
              onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
              placeholder="Enter username"
              className="w-full rounded border border-border bg-paper px-3 py-2.5 text-sm text-ink-950 placeholder:text-ink-400 focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium uppercase tracking-wide text-ink-500">Password</label>
            <input
              type="password" value={form.password} required
              onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
              placeholder="Enter password"
              className="w-full rounded border border-border bg-paper px-3 py-2.5 text-sm text-ink-950 placeholder:text-ink-400 focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber"
            />
          </div>

          {error && (
            <div className="rounded border border-verdict-bad/30 bg-verdict-bad/10 px-3 py-2 text-sm text-verdict-bad">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 rounded bg-amber py-3 text-sm font-medium text-steel transition-colors hover:bg-amber-hover hover:text-paper disabled:opacity-60"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}