'use client';

import { useState, useEffect, useCallback } from 'react';
import { API, Submission, fmt, diffPct, diffColorClass } from '../lib';
import StatusBadge from './StatusBadge';

export default function SubmissionsTab({ token, refreshKey }: { token: string; refreshKey: number }) {
  const [filter, setFilter] = useState('pending');
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/submissions?secret=${token}&status=${filter}`);
      if (!res.ok) { setLoading(false); return; }
      const data = await res.json();
      setSubmissions(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, [token, filter]);

  useEffect(() => { load(); }, [load, refreshKey]);

  const review = async (id: string, action: 'approve' | 'reject') => {
    const note = encodeURIComponent(notes[id] || '');
    await fetch(`${API}/admin/review?secret=${token}&submission_id=${id}&action=${action}&note=${note}`, {
      method: 'POST',
    });
    load();
  };

  return (
    <div>
      <div className="mb-5 flex items-center gap-2">
        {['all', 'pending', 'approved', 'rejected'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-4 py-1.5 text-xs font-bold capitalize transition-colors ${
              filter === f ? 'bg-steel text-paper' : 'border border-border bg-surface text-ink-500 hover:text-ink-950'
            }`}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-sm text-ink-500">{submissions.length} results</span>
      </div>

      {loading && <div className="py-16 text-center text-ink-500">Loading...</div>}
      {!loading && submissions.length === 0 && (
        <div className="py-16 text-center text-ink-400">No {filter} submissions.</div>
      )}

      <div className="flex flex-col gap-3">
        {submissions.map((sub) => (
          <div key={sub.id} className="rounded-md border border-border bg-surface p-5">
            <div className="mb-3.5 flex items-start justify-between">
              <div>
                <span className="text-[15px] font-bold uppercase text-ink-950">{sub.brand} {sub.model}</span>
                <span className="ml-2 text-sm text-ink-500">{sub.year} · {sub.fuel} · {sub.car_condition}</span>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={sub.status} />
                <span className="text-xs text-ink-400">{String(sub.timestamp).slice(0, 16)}</span>
              </div>
            </div>

            <div className="mb-3.5 grid grid-cols-4 gap-2.5">
              {[
                { label: 'USER PRICE', value: fmt(sub.user_price), colorClass: 'text-ink-950' },
                { label: 'MODEL PREDICTED', value: fmt(sub.predicted_price), colorClass: 'text-amber' },
                {
                  label: 'DIFFERENCE',
                  value: diffPct(sub.user_price, sub.predicted_price),
                  colorClass: diffColorClass(sub.user_price, sub.predicted_price),
                },
                {
                  label: 'MILEAGE / CC',
                  value: `${sub.mileage_km ? sub.mileage_km.toLocaleString() + ' km' : '—'} · ${sub.engine_cc ? sub.engine_cc + 'cc' : '—'}`,
                  colorClass: 'text-ink-950',
                },
              ].map((item, i) => (
                <div key={i} className="rounded bg-paper px-3.5 py-2.5">
                  <div className="mb-1 text-[10px] font-bold tracking-wide text-ink-500">{item.label}</div>
                  <div className={`text-sm font-bold ${item.colorClass}`}>{item.value}</div>
                </div>
              ))}
            </div>

            {sub.status === 'pending' && (
              <div className="flex items-center gap-2">
                <input
                  placeholder="Optional note..."
                  value={notes[sub.id] || ''}
                  onChange={(e) => setNotes((p) => ({ ...p, [sub.id]: e.target.value }))}
                  className="flex-1 rounded border border-border bg-paper px-3 py-2 text-sm text-ink-950 placeholder:text-ink-400 focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber"
                />
                <button
                  onClick={() => review(sub.id, 'approve')}
                  className="rounded bg-verdict-great px-5 py-2 text-xs font-bold text-paper transition-opacity hover:opacity-90"
                >
                  ✓ Approve
                </button>
                <button
                  onClick={() => review(sub.id, 'reject')}
                  className="rounded bg-verdict-bad px-5 py-2 text-xs font-bold text-paper transition-opacity hover:opacity-90"
                >
                  ✗ Reject
                </button>
              </div>
            )}

            {sub.status !== 'pending' && sub.admin_note && (
              <div className="mt-2 text-sm text-ink-500">Note: {sub.admin_note}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}