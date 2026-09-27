'use client';

import { useState, useEffect, useCallback } from 'react';
import { API, Stats } from '../lib';

export default function StatsTab({ token, refreshKey }: { token: string; refreshKey: number }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/stats?secret=${token}`);
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => { load(); }, [load, refreshKey]);

  if (loading && !stats) return <div className="py-16 text-center text-ink-500">Loading...</div>;
  if (!stats) return null;

  return (
    <div>
      <div className="mb-6 grid grid-cols-4 gap-4">
        {[
          { label: 'Total Queries', value: stats.total_queries, colorClass: 'text-ink-950' },
          { label: 'Total Submissions', value: stats.submissions.total, colorClass: 'text-ink-950' },
          { label: 'Pending Review', value: stats.submissions.pending, colorClass: 'text-amber' },
          { label: 'Approved', value: stats.submissions.approved, colorClass: 'text-verdict-great' },
        ].map((card) => (
          <div key={card.label} className="rounded-md border border-border bg-surface p-5">
            <div className="mb-2 text-xs font-bold text-ink-500">{card.label}</div>
            <div className={`font-mono text-3xl font-bold ${card.colorClass}`}>{card.value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-md border border-border bg-surface p-5">
        <div className="mb-4 text-sm font-semibold text-ink-950">Top searched brands</div>
        {stats.top_brands.map((b, i) => (
          <div key={b.brand} className="mb-2.5 flex items-center gap-3">
            <span className="w-5 text-xs text-ink-400">{i + 1}</span>
            <span className="flex-1 font-medium capitalize text-ink-950">{b.brand}</span>
            <div
              className="h-2 rounded-full bg-amber"
              style={{ width: `${Math.round((b.count / stats.top_brands[0].count) * 180)}px` }}
            />
            <span className="w-10 text-right text-sm text-ink-500">{b.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
