'use client';

import { useState } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import styles from './check.module.css';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:4000';
const ML_API  = process.env.NEXT_PUBLIC_ML_URL      ?? 'http://localhost:8000';

const BRANDS = [
  'audi','bmw','citroen','dacia','fiat','ford','haval','hyundai',
  'isuzu','kia','land rover','mazda','mercedes','mitsubishi','nissan',
  'opel','peugeot','porsche','renault','seat','skoda','suzuki',
  'toyota','volkswagen','other',
];
const FUELS  = ['gasoline','diesel','hybrid','electric'];
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
const vIcon  = (v: string) => v==='excellent_deal'?'🟢':v==='fair_price'?'🟡':v==='expensive'?'🟠':'🔴';
const vClass = (v: string, s: Record<string,string>) =>
  v==='excellent_deal'?s.green:v==='fair_price'?s.yellow:v==='expensive'?s.orange:s.red;

export default function CheckPage() {
  const [form, setForm] = useState({
    brand:'', model:'', year:'', fuel:'gasoline', body_style:'',
    car_condition:'medium', trim_level:'standard',
    mileage_km:'', engine_cc:'', seats:'', doors:'',
    user_price:'', mode:'buyer',
  });
  const [result,  setResult]  = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const set = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm(p => ({ ...p, [e.target.name]: e.target.value }));
    setResult(null); setError('');
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
      if (form.model)      body.model      = form.model.toLowerCase().trim();
      if (form.body_style) body.body_style = form.body_style;
      if (form.mileage_km) body.mileage_km = parseFloat(form.mileage_km);
      if (form.engine_cc)  body.engine_cc  = parseFloat(form.engine_cc);
      if (form.seats)      body.seats      = parseFloat(form.seats);
      if (form.doors)      body.doors      = parseFloat(form.doors);
      if (form.mode === 'buyer' && form.user_price) body.user_price = parseFloat(form.user_price);

      const res = await fetch(`${BACKEND}/api/check`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Server error. Is the backend running?');
      const data: Result = await res.json();
      setResult(data);

      fetch(`${BACKEND}/api/submit`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          brand: form.brand, model: form.model || null, year: parseInt(form.year),
          fuel: form.fuel, body_style: form.body_style || null,
          car_condition: form.car_condition, trim_level: form.trim_level,
          mileage_km: form.mileage_km ? parseFloat(form.mileage_km) : null,
          engine_cc:  form.engine_cc  ? parseFloat(form.engine_cc)  : null,
          user_price: form.user_price ? parseFloat(form.user_price) : data.predicted_price,
          predicted_price: data.predicted_price, segment: data.segment,
        }),
      }).catch(()=>{});

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const shareText = result
    ? result.verdict
      ? `AutoValu TN: ${form.brand} ${form.model} ${form.year} — ${result.verdict.label} (${result.verdict.diff_pct>0?'+':''}${result.verdict.diff_pct}%) | Market: ${fmt(result.predicted_price)}`
      : `AutoValu TN: ${form.brand} ${form.model} ${form.year} | Market: ${fmt(result.predicted_price)}`
    : '';

  return (
    <>
      <Header />
      <main className={styles.main}>
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>Check a car price</h1>
          <p className={styles.pageDesc}>Enter the car details and get the fair market price instantly.</p>
        </div>

        <div className={styles.layout}>
          <div className={styles.formSide}>

            <div className={styles.modeToggle}>
              <button type="button"
                className={`${styles.modeBtn} ${form.mode==='buyer'?styles.modeBtnActive:''}`}
                onClick={()=>setForm(p=>({...p,mode:'buyer',user_price:''}))}>
                🛒 Buyer — check a listing price
              </button>
              <button type="button"
                className={`${styles.modeBtn} ${form.mode==='seller'?styles.modeBtnActive:''}`}
                onClick={()=>setForm(p=>({...p,mode:'seller',user_price:''}))}>
                💰 Seller — what should I ask?
              </button>
            </div>

            <div className={styles.formCard}>
              <div className={styles.formHeader}>
                <span className={styles.formTitle}>Car details</span>
              </div>
              <form onSubmit={submit}>
                <div className={styles.formBody}>

                  <div className={styles.row}>
                    <div className={styles.field}>
                      <label>Brand *</label>
                      <select name="brand" value={form.brand} onChange={set} required>
                        <option value="">Select brand</option>
                        {BRANDS.map(b=><option key={b} value={b}>{cap(b)}</option>)}
                      </select>
                    </div>
                    <div className={styles.field}>
                      <label>Model</label>
                      <input name="model" value={form.model} onChange={set} type="text" placeholder="Golf 7, Clio 4..."/>
                    </div>
                  </div>

                  <div className={styles.row}>
                    <div className={styles.field}>
                      <label>Year *</label>
                      <input name="year" value={form.year} onChange={set} type="number" placeholder="2018" min="1960" max="2026" required/>
                    </div>
                    <div className={styles.field}>
                      <label>Mileage (km)</label>
                      <input name="mileage_km" value={form.mileage_km} onChange={set} type="number" placeholder="120 000"/>
                      <span className={styles.hint}>Optional — estimated if blank</span>
                    </div>
                  </div>

                  <div className={styles.row}>
                    <div className={styles.field}>
                      <label>Fuel</label>
                      <select name="fuel" value={form.fuel} onChange={set}>
                        {FUELS.map(f=><option key={f} value={f}>{cap(f)}</option>)}
                      </select>
                    </div>
                    <div className={styles.field}>
                      <label>Body type</label>
                      <select name="body_style" value={form.body_style} onChange={set}>
                        <option value="">Unknown</option>
                        {BODIES.map(b=><option key={b} value={b}>{cap(b)}</option>)}
                      </select>
                    </div>
                  </div>

                  <div className={styles.row}>
                    <div className={styles.field}>
                      <label>Condition</label>
                      <select name="car_condition" value={form.car_condition} onChange={set}>
                        {CONDITIONS.map(c=><option key={c} value={c}>{cap(c)}</option>)}
                      </select>
                    </div>
                    <div className={styles.field}>
                      <label>Trim level</label>
                      <select name="trim_level" value={form.trim_level} onChange={set}>
                        {TRIMS.map(t=><option key={t} value={t}>{cap(t)}</option>)}
                      </select>
                    </div>
                  </div>

                  <div className={styles.row}>
                    <div className={styles.field}>
                      <label>Engine CC</label>
                      <input name="engine_cc" value={form.engine_cc} onChange={set} type="number" placeholder="1600"/>
                    </div>
                    <div className={styles.field}>
                      <label>Seats</label>
                      <select name="seats" value={form.seats} onChange={set}>
                        <option value="">—</option>
                        {[2,3,4,5,7,8,9].map(n=><option key={n} value={n}>{n}</option>)}
                      </select>
                    </div>
                    <div className={styles.field}>
                      <label>Doors</label>
                      <select name="doors" value={form.doors} onChange={set}>
                        <option value="">—</option>
                        {[2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}
                      </select>
                    </div>
                  </div>

                  {form.mode==='buyer' && (
                    <div className={styles.priceSection}>
                      <div className={styles.priceSectionLabel}>💰 Price to check</div>
                      <div className={styles.field}>
                        <input name="user_price" value={form.user_price} onChange={set}
                          type="number" placeholder="Enter the price you saw (DT)"/>
                      </div>
                      <span className={styles.hint}>Leave blank to just see market value</span>
                    </div>
                  )}

                  {error && <p className={styles.error}>⚠ {error}</p>}
                </div>

                <div className={styles.formFooter}>
                  <button type="submit" className={styles.submitBtn} disabled={loading}>
                    {loading ? '⏳ Analyzing...' : form.mode==='buyer' ? '🔍 Check this price' : '💰 Get recommended price'}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* RESULT SIDE */}
          <div className={styles.resultSide}>
            {!result && !loading && (
              <div className={styles.resultEmpty}>
                <div className={styles.resultEmptyIcon}>🔍</div>
                <div className={styles.resultEmptyTitle}>Your result will appear here</div>
                <div className={styles.resultEmptyDesc}>Fill in the car details on the left and click Check this price.</div>
              </div>
            )}

            {result && (
              <div className={styles.result}>
                <div className={styles.priceCard}>
                  <div className={styles.priceCardTop}>
                    <div className={styles.priceCardLabel}>
                      {form.mode==='buyer' ? 'Fair market price' : 'Recommended listing price'}
                    </div>
                    <div className={styles.priceCardValue}>{fmt(result.predicted_price)}</div>
                    <div className={styles.priceCardRange}>
                      Range: {fmt(result.price_range.min)} — {fmt(result.price_range.max)}
                    </div>
                  </div>
                  {result.mileage_assumed && (
                    <div className={styles.priceCardBottom}>
                      <div className={styles.mileageNote}>
                        ⚠ Mileage estimated at {result.mileage_used.toLocaleString()} km
                      </div>
                    </div>
                  )}
                </div>

                {result.verdict && (
                  <div className={`${styles.verdictCard} ${vClass(result.verdict.verdict, styles)}`}>
                    <div className={styles.verdictInner}>
                      <span className={styles.verdictIcon}>{vIcon(result.verdict.verdict)}</span>
                      <div className={styles.verdictBody}>
                        <div className={styles.verdictTitle}>{result.verdict.label}</div>
                        <div className={styles.verdictMsg}>{result.verdict.message}</div>
                        {result.verdict.counter_offer && (
                          <div className={styles.counterOfferRow}>
                            <span className={styles.counterLabel}>Counter-offer:</span>
                            <span className={styles.counterValue}>{fmt(result.verdict.counter_offer)}</span>
                          </div>
                        )}
                      </div>
                      <span className={styles.diffBadge}>
                        {result.verdict.diff_pct > 0 ? '+':''}{result.verdict.diff_pct}%
                      </span>
                    </div>
                  </div>
                )}

                {form.mode==='seller' && (
                  <div className={styles.sellerCard}>
                    <div className={styles.sellerRow}><span>✅</span><span>List between <strong>{fmt(result.price_range.min)}</strong> and <strong>{fmt(result.price_range.max)}</strong></span></div>
                    <div className={styles.sellerRow}><span>⚠️</span><span>Above <strong>{fmt(result.price_range.max)}</strong> — buyers will scroll past</span></div>
                    <div className={styles.sellerRow}><span>💡</span><span>Below <strong>{fmt(result.price_range.min)}</strong> — leaving money on the table</span></div>
                  </div>
                )}

                <div className={`${styles.confidenceRow} ${styles[result.confidence.color]}`}>
                  <span>{result.confidence.level==='high'?'🎯':result.confidence.level==='medium'?'📊':'⚠️'}</span>
                  <span>{result.confidence.message}</span>
                </div>

                <div className={styles.shareRow}>
                  <button className={styles.copyBtn} onClick={()=>{
                    if (navigator.share) navigator.share({title:'AutoValu',text:shareText});
                    else { navigator.clipboard.writeText(shareText); alert('Copied!'); }
                  }}>📋 Copy</button>
                  <a className={styles.waBtn}
                    href={`https://wa.me/?text=${encodeURIComponent(shareText)}`}
                    target="_blank" rel="noopener noreferrer">📱 WhatsApp</a>
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