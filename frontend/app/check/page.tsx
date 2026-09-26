'use client';

import { useState } from 'react';
import {
  ShoppingCart, Wallet, Search, Loader2, AlertTriangle,
  CheckCircle2, Equal, CircleX, Target, BarChart3, Copy, MessageCircle,
} from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';

const API_URL = process.env.NEXT_PUBLIC_ML_URL ?? 'http://localhost:8000';

const BRANDS = [
  'audi','bmw','byd','chery','citroen','cupra','dacia','dfsk','dongfeng','ds',
  'fiat','ford','geely','gwm','honda','hyundai','isuzu','jaguar','jeep',
  'kia','land rover','lexus','mahindra','mazda','mercedes','mg','mini',
  'mitsubishi','nissan','opel','peugeot','porsche','renault','seat','skoda',
  'smart','ssangyong','suzuki','tesla','toyota','volkswagen','volvo','wallyscar','other',
].sort();

const FUELS = ['gasoline','diesel','hybrid','electric'];
const BODIES = ['sedan','hatchback','wagon','coupe','convertible','suv 4x4','suv 4x2','crossover','pickup 4x4','pickup 4x2','mpv','light commercial','heavy commercial'];
const CONDITIONS = ['good','medium','bad'];
const TRIMS = ['standard','amg','m','r line','s line','gti','rs','raptor','wildtrack','alpine','quattro','imported','other'];

type Verdict = {
  verdict: string; label: string; color: string;
  diff_pct: number; message: string; counter_offer: number | null;
};
type Result = {
  predicted_price: number;
  price_range: { min: number; max: number };
  confidence: { level: string; message: string; color: string };
  verdict: Verdict | null;
  mileage_assumed: boolean;
  mileage_used: number;
  segment: string;
};

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const fmt = (n: number) => n.toLocaleString('fr-TN') + ' DT';
const clamp = (n: number, min: number, max: number) => Math.min(Math.max(n, min), max);

const VERDICT_STYLES: Record<string, { bg: string; text: string; dot: string; Icon: typeof CheckCircle2 }> = {
  excellent_deal: { bg: 'bg-verdict-great/10', text: 'text-verdict-great', dot: 'bg-verdict-great', Icon: CheckCircle2 },
  fair_price:     { bg: 'bg-verdict-fair/10',  text: 'text-verdict-fair',  dot: 'bg-verdict-fair',  Icon: Equal },
  expensive:      { bg: 'bg-verdict-steep/10', text: 'text-verdict-steep', dot: 'bg-verdict-steep', Icon: AlertTriangle },
  overpriced:     { bg: 'bg-verdict-bad/10',   text: 'text-verdict-bad',   dot: 'bg-verdict-bad',   Icon: CircleX },
};

const CONFIDENCE_STYLES: Record<string, { text: string; Icon: typeof Target }> = {
  high:   { text: 'text-verdict-great', Icon: Target },
  medium: { text: 'text-verdict-fair',  Icon: BarChart3 },
  low:    { text: 'text-verdict-steep', Icon: AlertTriangle },
};

const inputClass = 'w-full rounded border border-border bg-paper px-3 py-2.5 text-sm text-ink-950 placeholder:text-ink-400 focus:border-amber focus:outline-none focus:ring-1 focus:ring-amber transition-colors';
const labelClass = 'mb-1.5 block text-xs font-medium text-ink-500';

export default function CheckPage() {
  const [form, setForm] = useState({
    brand: '', model: '', year: '', fuel: 'gasoline', body_style: '',
    car_condition: 'medium', trim_level: 'standard',
    mileage_km: '', engine_cc: '', seats: '', doors: '',
    user_price: '', mode: 'buyer' as 'buyer' | 'seller',
  });
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
    setResult(null);
    setError('');
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.brand || !form.year) { setError('Brand and year are required.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const body: Record<string, unknown> = {
        brand: form.brand, year: parseInt(form.year),
        fuel: form.fuel, car_condition: form.car_condition, trim_level: form.trim_level,
      };
      if (form.model) body.model = form.model.toLowerCase().trim();
      if (form.body_style) body.body_style = form.body_style;
      if (form.mileage_km) body.mileage_km = parseFloat(form.mileage_km);
      if (form.engine_cc) body.engine_cc = parseFloat(form.engine_cc);
      if (form.seats) body.seats = parseFloat(form.seats);
      if (form.doors) body.doors = parseFloat(form.doors);
      if (form.mode === 'buyer' && form.user_price) body.user_price = parseFloat(form.user_price);

      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Server error. Is the backend running?');
      const data: Result = await res.json();
      setResult(data);

      fetch(`${API_URL}/submit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand: form.brand, model: form.model || null, year: parseInt(form.year),
          fuel: form.fuel, body_style: form.body_style || null,
          car_condition: form.car_condition, trim_level: form.trim_level,
          mileage_km: form.mileage_km ? parseFloat(form.mileage_km) : null,
          engine_cc: form.engine_cc ? parseFloat(form.engine_cc) : null,
          user_price: form.user_price ? parseFloat(form.user_price) : data.predicted_price,
          predicted_price: data.predicted_price, segment: data.segment,
        }),
      }).catch(() => {});
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const shareText = result
    ? result.verdict
      ? `AutoValu TN: ${form.brand} ${form.model} ${form.year} - ${result.verdict.label} (${result.verdict.diff_pct > 0 ? '+' : ''}${result.verdict.diff_pct}%) | Market: ${fmt(result.predicted_price)}`
      : `AutoValu TN: ${form.brand} ${form.model} ${form.year} | Market: ${fmt(result.predicted_price)}`
    : '';

  // marker position within the range bar: user's price if a verdict was computed, else the predicted price itself
  const markerValue = result?.verdict ? parseFloat(form.user_price) : result?.predicted_price;
  const markerPct = result && markerValue != null && !isNaN(markerValue)
    ? clamp(((markerValue - result.price_range.min) / (result.price_range.max - result.price_range.min)) * 100, 0, 100)
    : null;
  const markerStyle = result?.verdict ? VERDICT_STYLES[result.verdict.verdict] : null;

  return (
    <>
      <Header />
      <main className="min-h-screen bg-paper text-ink-950">
        <div className="mx-auto max-w-6xl px-6 pt-14">
          <h1 className="font-display text-4xl font-bold uppercase tracking-tight">Check a car price</h1>
          <p className="mt-2 text-ink-500">Enter the car details and get the fair market price instantly.</p>
        </div>

        <div className="mx-auto grid max-w-6xl gap-8 px-6 py-10 lg:grid-cols-[1.15fr_1fr]">
          {/* FORM SIDE */}
          <div>
            <div className="mb-6 grid grid-cols-2 gap-1 rounded-lg border border-border bg-surface p-1">
              <button
                type="button"
                onClick={() => setForm((p) => ({ ...p, mode: 'buyer', user_price: '' }))}
                className={`flex items-center justify-center gap-2 rounded-md py-2.5 text-sm font-medium transition-colors ${
                  form.mode === 'buyer' ? 'bg-steel text-paper' : 'text-ink-500 hover:text-ink-950'
                }`}
              >
                <ShoppingCart className="h-4 w-4" /> Buyer
              </button>
              <button
                type="button"
                onClick={() => setForm((p) => ({ ...p, mode: 'seller', user_price: '' }))}
                className={`flex items-center justify-center gap-2 rounded-md py-2.5 text-sm font-medium transition-colors ${
                  form.mode === 'seller' ? 'bg-steel text-paper' : 'text-ink-500 hover:text-ink-950'
                }`}
              >
                <Wallet className="h-4 w-4" /> Seller
              </button>
            </div>

            <div className="rounded-md border border-border bg-surface p-6">
              <form onSubmit={submit} className="flex flex-col gap-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Brand *</label>
                    <select name="brand" value={form.brand} onChange={set} required className={inputClass}>
                      <option value="">Select brand</option>
                      {BRANDS.map((b) => <option key={b} value={b}>{cap(b)}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Model</label>
                    <input name="model" value={form.model} onChange={set} type="text" placeholder="Golf 7, Clio 4..." className={inputClass} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Year *</label>
                    <input name="year" value={form.year} onChange={set} type="number" placeholder="2018" min="1960" max="2026" required className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Mileage (km)</label>
                    <input name="mileage_km" value={form.mileage_km} onChange={set} type="number" placeholder="120 000" className={inputClass} />
                    <span className="mt-1 block text-xs text-ink-400">Optional, estimated if blank</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Fuel</label>
                    <select name="fuel" value={form.fuel} onChange={set} className={inputClass}>
                      {FUELS.map((f) => <option key={f} value={f}>{cap(f)}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Body type</label>
                    <select name="body_style" value={form.body_style} onChange={set} className={inputClass}>
                      <option value="">Unknown</option>
                      {BODIES.map((b) => <option key={b} value={b}>{cap(b)}</option>)}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Condition</label>
                    <select name="car_condition" value={form.car_condition} onChange={set} className={inputClass}>
                      {CONDITIONS.map((c) => <option key={c} value={c}>{cap(c)}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Trim level</label>
                    <select name="trim_level" value={form.trim_level} onChange={set} className={inputClass}>
                      {TRIMS.map((t) => <option key={t} value={t}>{cap(t)}</option>)}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className={labelClass}>Engine CC</label>
                    <input name="engine_cc" value={form.engine_cc} onChange={set} type="number" placeholder="1600" className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Seats</label>
                    <select name="seats" value={form.seats} onChange={set} className={inputClass}>
                      <option value="">-</option>
                      {[2,3,4,5,7,8,9].map((n) => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Doors</label>
                    <select name="doors" value={form.doors} onChange={set} className={inputClass}>
                      <option value="">-</option>
                      {[2,3,4,5].map((n) => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </div>
                </div>

                {form.mode === 'buyer' && (
                  <div className="rounded border border-border bg-paper p-4">
                    <label className={labelClass}>Price to check</label>
                    <input name="user_price" value={form.user_price} onChange={set} type="number" placeholder="Enter the price you saw (DT)" className={inputClass} />
                    <span className="mt-1 block text-xs text-ink-400">Leave blank to just see market value</span>
                  </div>
                )}

                {error && (
                  <div className="flex items-center gap-2 text-sm text-verdict-bad">
                    <AlertTriangle className="h-4 w-4 shrink-0" /> {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center justify-center gap-2 rounded bg-amber py-3 text-sm font-medium text-steel transition-colors hover:bg-amber-hover hover:text-paper disabled:opacity-60"
                >
                  {loading ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing...</>
                  ) : form.mode === 'buyer' ? (
                    <><Search className="h-4 w-4" /> Check this price</>
                  ) : (
                    <><Wallet className="h-4 w-4" /> Get recommended price</>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* RESULT SIDE */}
          <div>
            {!result && !loading && (
              <div className="flex h-full min-h-[320px] flex-col items-center justify-center rounded-md border border-dashed border-border p-10 text-center">
                <Search className="h-8 w-8 text-ink-400" />
                <div className="mt-4 font-medium text-ink-950">Your result will appear here</div>
                <div className="mt-1 text-sm text-ink-500">Fill in the car details and click check price.</div>
              </div>
            )}

            {result && (
              <div className="flex flex-col gap-4">
                <div className="rounded-md border border-border bg-surface p-6">
                  <div className="text-xs font-medium text-ink-500">
                    {form.mode === 'buyer' ? 'Fair market price' : 'Recommended listing price'}
                  </div>
                  <div className="mt-1 font-mono text-4xl font-semibold text-ink-950">{fmt(result.predicted_price)}</div>

                  <div className="mt-4">
                    <div className="relative h-1.5 rounded-full bg-border">
                      {markerPct !== null && (
                        <>
                          <div
                            className={`absolute inset-y-0 left-0 rounded-full ${markerStyle ? markerStyle.dot : 'bg-amber'}`}
                            style={{ width: `${markerPct}%` }}
                          />
                          <div
                            className={`absolute top-1/2 h-3 w-3 -translate-y-1/2 -translate-x-1/2 rounded-full border-2 border-surface ${markerStyle ? markerStyle.dot : 'bg-amber'}`}
                            style={{ left: `${markerPct}%` }}
                          />
                        </>
                      )}
                    </div>
                    <div className="mt-2 flex justify-between font-mono text-xs text-ink-500">
                      <span>{fmt(result.price_range.min)}</span>
                      <span>{fmt(result.price_range.max)}</span>
                    </div>
                  </div>

                  {result.mileage_assumed && (
                    <div className="mt-4 flex items-center gap-2 border-t border-border pt-4 text-xs text-ink-500">
                      <AlertTriangle className="h-3.5 w-3.5" /> Mileage estimated at {result.mileage_used.toLocaleString()} km
                    </div>
                  )}
                </div>

                {result.verdict && (() => {
                  const v = VERDICT_STYLES[result.verdict.verdict];
                  const VIcon = v.Icon;
                  return (
                    <div className={`rounded-md border border-border p-5 ${v.bg}`}>
                      <div className="flex items-start gap-3">
                        <VIcon className={`h-5 w-5 shrink-0 ${v.text}`} />
                        <div className="flex-1">
                          <div className={`font-medium ${v.text}`}>{result.verdict.label}</div>
                          <div className="mt-1 text-sm text-ink-500">{result.verdict.message}</div>
                          {result.verdict.counter_offer && (
                            <div className="mt-3 flex items-center gap-2 text-sm">
                              <span className="text-ink-500">Counter-offer:</span>
                              <span className="font-mono font-medium text-ink-950">{fmt(result.verdict.counter_offer)}</span>
                            </div>
                          )}
                        </div>
                        <span className={`font-mono text-sm ${v.text}`}>
                          {result.verdict.diff_pct > 0 ? '+' : ''}{result.verdict.diff_pct}%
                        </span>
                      </div>
                    </div>
                  );
                })()}

                {form.mode === 'seller' && (
                  <div className="rounded-md border border-border bg-surface p-5">
                    <div className="flex items-start gap-3 text-sm text-ink-500">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-verdict-great" />
                      List between <strong className="text-ink-950">{fmt(result.price_range.min)}</strong> and <strong className="text-ink-950">{fmt(result.price_range.max)}</strong>
                    </div>
                    <div className="mt-3 flex items-start gap-3 text-sm text-ink-500">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-verdict-steep" />
                      Above <strong className="text-ink-950">{fmt(result.price_range.max)}</strong>, buyers will scroll past
                    </div>
                    <div className="mt-3 flex items-start gap-3 text-sm text-ink-500">
                      <BarChart3 className="mt-0.5 h-4 w-4 shrink-0 text-amber" />
                      Below <strong className="text-ink-950">{fmt(result.price_range.min)}</strong>, you&apos;re leaving money on the table
                    </div>
                  </div>
                )}

                {(() => {
                  const c = CONFIDENCE_STYLES[result.confidence.level] ?? CONFIDENCE_STYLES.low;
                  const CIcon = c.Icon;
                  return (
                    <div className={`flex items-center gap-2 text-sm ${c.text}`}>
                      <CIcon className="h-4 w-4" /> {result.confidence.message}
                    </div>
                  );
                })()}

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      if (navigator.share) navigator.share({ title: 'AutoValu', text: shareText });
                      else { navigator.clipboard.writeText(shareText); alert('Copied!'); }
                    }}
                    className="flex flex-1 items-center justify-center gap-2 rounded border border-border py-2.5 text-sm text-ink-500 transition-colors hover:border-steel hover:text-ink-950"
                  >
                    <Copy className="h-4 w-4" /> Copy
                  </button>
                  <a
                    href={`https://wa.me/?text=${encodeURIComponent(shareText)}`}
                    target="_blank" rel="noopener noreferrer"
                    className="flex flex-1 items-center justify-center gap-2 rounded bg-steel py-2.5 text-sm font-medium text-paper transition-colors hover:bg-steel-hover"
                  >
                    <MessageCircle className="h-4 w-4" /> WhatsApp
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}