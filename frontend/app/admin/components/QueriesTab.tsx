'use client';

import { useState, useEffect, useCallback } from 'react';
import { API, fmt } from '../lib';

export default function QueriesTab({ token, refreshKey }: { token: string; refreshKey: number }) {
  const [queries, setQueries] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/queries?secret=${token}&limit=100`);
      if (!res.ok) { setLoading(false); return; }
      const data = await res.json();
      setQueries(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => { load(); }, [load, refreshKey]);

  return (
    <div>
      <div className="mb-3.5 text-sm text-ink-500">
        Last 100 user queries every check including ones without a user price
      </div>
      <div className="overflow-hidden rounded-md border border-border bg-surface">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-paper">
              {['Time', 'Brand', 'Model', 'Year', 'Mileage', 'Predicted', 'User Price', 'Segment', 'KNN'].map((h) => (
                <th key={h} className="px-3.5 py-2.5 text-left text-[11px] font-bold text-ink-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {queries.map((q, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="whitespace-nowrap px-3.5 py-2.5 text-ink-400">{String(q.timestamp || '').slice(0, 16)}</td>
                <td className="px-3.5 py-2.5 font-semibold capitalize text-ink-950">{String(q.brand || '')}</td>
                <td className="px-3.5 py-2.5 text-ink-500">{String(q.model || '—')}</td>
                <td className="px-3.5 py-2.5 text-ink-950">{String(q.year || '')}</td>
                <td className="px-3.5 py-2.5 text-ink-500">
                  {q.mileage_km ? Number(q.mileage_km).toLocaleString() : '—'}
                </td>
                <td className="px-3.5 py-2.5 font-bold text-amber">
                  {q.predicted_price ? fmt(Number(q.predicted_price)) : '—'}
                </td>
                <td className="px-3.5 py-2.5 text-ink-950">
                  {q.user_price ? fmt(Number(q.user_price)) : '—'}
                </td>
                <td className="px-3.5 py-2.5">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                      q.segment === 'mid' ? 'bg-verdict-fair/10 text-verdict-fair' : 'bg-verdict-great/10 text-verdict-great'
                    }`}
                  >
                    {String(q.segment || '')}
                  </span>
                </td>
                <td className={`px-3.5 py-2.5 text-xs ${q.knn_price ? 'text-verdict-great' : 'text-ink-400'}`}>
                  {q.knn_price ? `${Number(q.knn_price).toLocaleString()} DT` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {queries.length === 0 && !loading && (
          <div className="py-16 text-center text-ink-400">No queries yet.</div>
        )}
      </div>
    </div>
  );
}
