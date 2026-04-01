'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from './components/Header';
import Footer from './components/Footer';
import styles from './page.module.css';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:4000';
const ML_API  = process.env.NEXT_PUBLIC_ML_URL      ?? 'http://localhost:8000';

type Stats = {
  total_checks: number;
  top_brands  : { brand: string; count: number }[];
  top_models  : { model: string; count: number }[];
  avg_price   : number;
};

const fmt = (n: number) => n.toLocaleString('fr-TN');

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Enter car details',
    desc: 'Brand, model, year, mileage, fuel, condition fill what you know. Mileage is optional.',
    icon: '📋',
  },
  {
    step: '02',
    title: 'AI analyzes the market',
    desc: 'Our XGBoost model trained on thousands of real Tunisian listings predicts the fair market price instantly.',
    icon: '🧠',
  },
  {
    step: '03',
    title: 'Get your verdict',
    desc: 'See the market price, a confidence range, and if you entered a listing price an instant deal / fair / overpriced verdict.',
    icon: '🎯',
  },
  {
    step: '04',
    title: 'Negotiate with confidence',
    desc: 'If the price is too high, we give you a data-backed counter-offer. Stop guessing. Start winning.',
    icon: '💪',
  },
];

const FEATURES = [
  { icon:'🇹🇳', title:'Tunisia-specific',   desc:'Trained exclusively on Tunisian market data. Not European prices, not average Arab market Tunisia only.' },
  { icon:'⚡', title:'Instant results',     desc:'No waiting. Enter specs and get your answer in under 2 seconds.' },
  { icon:'🎯', title:'Dual AI system',      desc:'XGBoost machine learning model + KNN nearest-neighbor search work together for better accuracy.' },
  { icon:'📊', title:'Buyer & Seller mode', desc:'Whether you\'re buying or selling, we give you the right information for your situation.' },
  { icon:'🔒', title:'No registration',     desc:'No account needed. No email. No tracking. Just check the price and go.' },
  { icon:'📱', title:'Share instantly',     desc:'Copy your result or share directly on WhatsApp with one tap.' },
];

export default function LandingPage() {
  const [stats, setStats]   = useState<Stats | null>(null);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    fetch(`${ML_API}/stats/public`)
      .then(r => r.json())
      .then(d => {
        setStats(d);
        setHasData(d.total_checks > 0);
      })
      .catch(() => setHasData(false));
  }, []);

  return (
    <>
      <Header />
      <main className={styles.landing}>

        {/* HERO */}
        <section className={styles.landingHero}>
          <div className={styles.landingHeroInner}>
            <div className={styles.heroBadge}>🇹🇳 Made for Tunisia</div>
            <h1 className={styles.landingTitle}>
              Stop guessing.<br/>
              <span className={styles.landingTitleAccent}>Know the real price.</span>
            </h1>
            <p className={styles.landingSubtitle}>
              AutoValu uses AI trained on thousands of real Tunisian car listings
              to tell you if a used car is a great deal, fairly priced, or overpriced in seconds.
            </p>
            <div className={styles.heroActions}>
              <Link href="/check" className={styles.heroCtaPrimary}>
                Check a car price →
              </Link>
              <a href="#how-it-works" className={styles.heroCtaSecondary}>
                How it works
              </a>
            </div>
            <p className={styles.heroNote}>Free · No account needed · Instant results</p>
          </div>

          <div className={styles.heroVisual}>
            <div className={styles.demoCard}>
              <div className={styles.demoCardHeader}>Market price</div>
              <div className={styles.demoCardPrice}>56 500 DT</div>
              <div className={styles.demoCardRange}>Range: 49 800 — 60 200 DT</div>
              <div className={styles.demoVerdict}>
                <span className={styles.demoVerdictDot} style={{background:'#10B981'}}/>
                <span style={{color:'#065F46',fontWeight:700}}>Excellent deal</span>
                <span className={styles.demoVerdictBadge} style={{background:'#D1FAE5',color:'#065F46'}}>−6.2%</span>
              </div>
              <div className={styles.demoRow}><span>Brand</span><strong>Volkswagen</strong></div>
              <div className={styles.demoRow}><span>Model</span><strong>Golf 7</strong></div>
              <div className={styles.demoRow}><span>Year</span><strong>2017</strong></div>
              <div className={styles.demoRow}><span>Mileage</span><strong>120 000 km</strong></div>
              <div className={styles.demoConfidence}>🎯 High confidence</div>
            </div>
          </div>
        </section>

        {/* LIVE STATS — only shown if there is real data */}
        {hasData && stats && stats.total_checks > 0 && (
          <section className={styles.statsSection}>
            <div className={styles.sectionInner}>
              <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                  <div className={styles.statValue}>{fmt(stats.total_checks)}+</div>
                  <div className={styles.statLabel}>Price checks done</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statValue}>{stats.top_brands.length > 0 ? fmt(Math.round(stats.avg_price)) + ' DT' : '—'}</div>
                  <div className={styles.statLabel}>Average checked price</div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statValue}>{stats.top_brands.length}</div>
                  <div className={styles.statLabel}>Car brands covered</div>
                </div>
              </div>

              {stats.top_brands.length > 0 && (
                <div className={styles.chartsRow}>
                  <div className={styles.chartCard}>
                    <div className={styles.chartTitle}>Most checked brands</div>
                    {stats.top_brands.map((b, i) => (
                      <div key={b.brand} className={styles.barRow}>
                        <span className={styles.barRank}>{i + 1}</span>
                        <span className={styles.barLabel}>{b.brand.charAt(0).toUpperCase() + b.brand.slice(1)}</span>
                        <div className={styles.barTrack}>
                          <div
                            className={styles.barFill}
                            style={{ width: `${Math.round(b.count / stats.top_brands[0].count * 100)}%` }}
                          />
                        </div>
                        <span className={styles.barCount}>{b.count}</span>
                      </div>
                    ))}
                  </div>

                  {stats.top_models.length > 0 && (
                    <div className={styles.chartCard}>
                      <div className={styles.chartTitle}>Most checked models</div>
                      {stats.top_models.map((m, i) => (
                        <div key={m.model} className={styles.barRow}>
                          <span className={styles.barRank}>{i + 1}</span>
                          <span className={styles.barLabel}>{m.model.charAt(0).toUpperCase() + m.model.slice(1)}</span>
                          <div className={styles.barTrack}>
                            <div
                              className={styles.barFill}
                              style={{ width: `${Math.round(m.count / stats.top_models[0].count * 100)}%` }}
                            />
                          </div>
                          <span className={styles.barCount}>{m.count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}

        {/* HOW IT WORKS */}
        <section className={styles.howSection} id="how-it-works">
          <div className={styles.sectionInner}>
            <div className={styles.sectionLabel}>Simple process</div>
            <h2 className={styles.sectionTitle}>How AutoValu works</h2>
            <p className={styles.sectionDesc}>
              Four steps from curiosity to confidence.
            </p>
            <div className={styles.stepsGrid}>
              {HOW_IT_WORKS.map(s => (
                <div key={s.step} className={styles.stepCard}>
                  <div className={styles.stepTop}>
                    <span className={styles.stepIcon}>{s.icon}</span>
                    <span className={styles.stepNum}>{s.step}</span>
                  </div>
                  <div className={styles.stepTitle}>{s.title}</div>
                  <div className={styles.stepDesc}>{s.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FEATURES */}
        <section className={styles.featuresSection}>
          <div className={styles.sectionInner}>
            <div className={styles.sectionLabel}>Why AutoValu</div>
            <h2 className={styles.sectionTitle}>Built for the Tunisian market</h2>
            <div className={styles.featuresGrid}>
              {FEATURES.map(f => (
                <div key={f.title} className={styles.featureCard}>
                  <div className={styles.featureIcon}>{f.icon}</div>
                  <div className={styles.featureTitle}>{f.title}</div>
                  <div className={styles.featureDesc}>{f.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* TECH SECTION */}
        <section className={styles.techSection}>
          <div className={styles.sectionInner}>
            <div className={styles.techInner}>
              <div className={styles.techText}>
                <div className={styles.sectionLabel}>Under the hood</div>
                <h2 className={styles.techTitle}>Real AI. Real data. Real results.</h2>
                <p className={styles.techDesc}>
                  AutoValu uses XGBoost the same algorithm used in professional
                  financial and pricing models worldwide. Trained on thousands of
                  verified Tunisian car listings collected from Tayara and automobile.tn.
                </p>
                <div className={styles.techPoints}>
                  <div className={styles.techPoint}><span className={styles.techDot}/>XGBoost regression model for price prediction</div>
                  <div className={styles.techPoint}><span className={styles.techDot}/>KNN nearest-neighbor search for real comparable cars</div>
                  <div className={styles.techPoint}><span className={styles.techDot}/>Two-segment model: budget vs mid-premium cars</div>
                  <div className={styles.techPoint}><span className={styles.techDot}/>Smart routing by brand tier and price range</div>
                  <div className={styles.techPoint}><span className={styles.techDot}/>Trained on 3,300+ real Tunisian market listings</div>
                </div>
              </div>
              <div className={styles.techVisual}>
                <div className={styles.techCard}>
                  <div className={styles.techCardRow}>
                    <span className={styles.techCardLabel}>Algorithm</span>
                    <span className={styles.techCardValue}>XGBoost + KNN</span>
                  </div>
                  <div className={styles.techCardRow}>
                    <span className={styles.techCardLabel}>Training data</span>
                    <span className={styles.techCardValue}>3 300+ listings</span>
                  </div>
                  <div className={styles.techCardRow}>
                    <span className={styles.techCardLabel}>Market</span>
                    <span className={styles.techCardValue}>Tunisia only</span>
                  </div>
                  <div className={styles.techCardRow}>
                    <span className={styles.techCardLabel}>Avg. accuracy</span>
                    <span className={styles.techCardValue}>~84%</span>
                  </div>
                  <div className={styles.techCardRow}>
                    <span className={styles.techCardLabel}>Price range</span>
                    <span className={styles.techCardValue}>2 500 — 580 000 DT</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FINAL CTA */}
        <section className={styles.ctaSection}>
          <div className={styles.sectionInner}>
            <h2 className={styles.ctaTitle}>Ready to check a price?</h2>
            <p className={styles.ctaDesc}>
              Free, instant, no registration. Just enter the car specs and find out.
            </p>
            <Link href="/check" className={styles.ctaBtnLarge}>
              Check a car price →
            </Link>
          </div>
        </section>

      </main>
      <Footer />
    </>
  );
}