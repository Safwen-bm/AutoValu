"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  MapPin,
  GitCompare,
  Gauge,
  Scale,
  Zap,
  Unlock,
} from "lucide-react";
import Header from "./components/Header";
import Footer from "./components/Footer";

const API_URL = process.env.NEXT_PUBLIC_ML_URL ?? "http://localhost:8000";

type Stats = {
  total_checks: number;
  top_brands: { brand: string; count: number }[];
  top_models: { model: string; count: number }[];
  avg_price: number;
};

type Health = {
  segments: {
    budget: { mae: number; mape: number; rows: number };
    mid: { mae: number; mape: number; rows: number };
  };
};

const fmt = (n: number) => n.toLocaleString("fr-TN");

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Enter car details",
    desc: "Brand, model, year, mileage, fuel, condition. Mileage is optional.",
  },
  {
    step: "02",
    title: "Analyze the market",
    desc: "The model compares your car against real Tunisian listings for the same segment.",
  },
  {
    step: "03",
    title: "Get your valuation",
    desc: "A market price, a low-high range, and a verdict if you gave a listing price.",
  },
  {
    step: "04",
    title: "Negotiate with confidence",
    desc: "If the price is high, you get a data-backed counter-offer.",
  },
];

const FEATURES = [
  {
    title: "Real Tunisian market data",
    desc: "Modeled on local listings only, not global or regional averages.",
    icon: MapPin,
  },
  {
    title: "Comparable vehicles",
    desc: "Nearest-neighbor matching finds real listings closest to your car.",
    icon: GitCompare,
  },
  {
    title: "Market price range",
    desc: "See the full low-to-high range, not just a single number.",
    icon: Gauge,
  },
  {
    title: "Buyer & seller analysis",
    desc: "Check a listing price, or get a recommended asking price.",
    icon: Scale,
  },
  {
    title: "Instant valuation",
    desc: "Results in under two seconds, no waiting.",
    icon: Zap,
  },
  {
    title: "No registration required",
    desc: "No account or email needed to check a price.",
    icon: Unlock,
  },
];

const PIPELINE = [
  "3,373+ listings",
  "Data cleaning",
  "Feature engineering",
  "XGBoost price model + KNN comparable vehicles",
  "Market valuation",
];

export default function LandingPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [hasData, setHasData] = useState(false);
  const [avgMape, setAvgMape] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/stats/public`)
      .then((r) => r.json())
      .then((d) => {
        setStats(d);
        setHasData(d.total_checks > 0);
      })
      .catch(() => setHasData(false));

    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then((d: Health) => {
        const avg = (d.segments.budget.mape + d.segments.mid.mape) / 2;
        setAvgMape(avg.toFixed(1));
      })
      .catch(() => {});
  }, []);

  return (
    <>
      <Header />
      <main className="bg-paper text-ink-950">
        {/* HERO — dark band, matches the image's own gunmetal background */}
        <section className="relative min-h-[calc(100vh-72px)] overflow-hidden bg-steel">
          <div
            className="absolute inset-0 bg-cover bg-left"
            style={{ backgroundImage: "url('/hero-bg.jpg')" }}
            aria-hidden="true"
          />
          {/* small contrast margin behind the text column — the image itself is already dark here, this just guarantees it */}
          <div
            className="absolute inset-0 bg-gradient-to-r from-steel/50 via-steel/5 to-transparent"
            aria-hidden="true"
          />
          {/* blend the bottom edge into the paper section below */}
          <div
            className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-b from-transparent to-paper"
            aria-hidden="true"
          />

          <div className="relative mx-auto grid max-w-6xl items-center gap-16 px-6 pb-20 pt-16 lg:grid-cols-2 lg:pt-24">
            <div>
              <p className="text-sm text-surface-alt">
                Used-car pricing, built for Tunisia
              </p>
              <h1 className="mt-3 font-display text-6xl font-bold uppercase leading-[0.95] tracking-tight text-paper sm:text-7xl">
                Don&apos;t overpay.
                <br />
                Don&apos;t undersell.
              </h1>
              <p className="mt-6 max-w-md text-base leading-relaxed text-surface-alt">
                AutoValu checks a car&apos;s price against thousands of real
                Tunisian listings, so you know where you stand before you buy or
                sell.
              </p>
              <div className="mt-8">
                <Link
                  href="/check"
                  className="inline-flex items-center gap-2 rounded bg-amber px-5 py-3 text-sm font-medium text-steel transition-colors hover:bg-amber-hover hover:text-paper"
                >
                  Check a car price <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            {/* VALUATION CARD — floats over the dark image like a HUD readout; amber frame instead of steel so it doesn't vanish into the background */}
            <div className="relative rotate-[-0.6deg] rounded-md border-2 border-amber/50 bg-surface p-6 shadow-xl shadow-black/30">
              <div className="absolute -left-[14px] top-9 h-7 w-7 rounded-full border-2 border-amber/50 bg-steel" />
              <div className="text-sm text-ink-500">Market valuation</div>
              <div className="mt-2 text-lg font-semibold text-ink-950">
                Volkswagen Golf 7 · 2017
              </div>
              <div className="text-sm text-ink-500">120,000 km · Diesel</div>

              <div className="mt-6">
                <div className="text-xs font-medium text-ink-500">
                  Estimated market price
                </div>
                <div className="mt-1 font-mono text-5xl font-semibold text-ink-950">
                  56,500 DT
                </div>
              </div>

              <div className="mt-6">
                <div className="relative h-1.5 rounded-full bg-border">
                  <div
                    className="absolute top-1/2 h-3 w-3 -translate-y-1/2 -translate-x-1/2 rounded-full border-2 border-surface bg-verdict-great"
                    style={{ left: "31%" }}
                  />
                  <div
                    className="absolute top-1/2 h-3 w-3 -translate-y-1/2 -translate-x-1/2 rounded-full border-2 border-surface bg-steel"
                    style={{ left: "64%" }}
                  />
                </div>
                <div className="mt-2 flex justify-between text-[11px] font-medium text-ink-500">
                  <span>Low</span>
                  <span>Market</span>
                  <span>High</span>
                </div>
                <div className="mt-1 flex justify-between font-mono text-xs text-ink-500">
                  <span>49,800</span>
                  <span>56,500</span>
                  <span>60,200</span>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between rounded bg-verdict-great-bg px-4 py-3">
                <div>
                  <div className="text-sm font-semibold text-verdict-great">
                    Good deal
                  </div>
                  <div className="text-xs text-ink-500">
                    Asking price: 53,000 DT
                  </div>
                </div>
                <div className="font-mono text-sm font-semibold text-verdict-great">
                  -6.2%
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-border pt-4 text-sm">
                <span className="text-ink-500">Market confidence</span>
                <span className="font-semibold text-ink-950">High</span>
              </div>
            </div>
          </div>
        </section>

        {/* LIVE ACTIVITY — one instrument-cluster panel instead of three matching cards */}
        {hasData && stats && stats.total_checks > 0 && (
          <section className="border-t border-border">
            <div className="mx-auto max-w-6xl px-6 py-16">
              <h2 className="font-display text-3xl font-bold uppercase tracking-tight text-ink-950">
                On the dashboard right now
              </h2>

              <div className="mt-8 grid grid-cols-1 divide-y divide-border rounded-md border border-steel bg-surface sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                <div className="p-6">
                  <div className="font-mono text-3xl font-semibold text-ink-950">
                    {fmt(stats.total_checks)}+
                  </div>
                  <div className="mt-1 text-sm text-ink-500">
                    Price checks run
                  </div>
                </div>
                <div className="p-6">
                  <div className="font-mono text-3xl font-semibold text-ink-950">
                    {stats.top_brands.length > 0
                      ? `${fmt(Math.round(stats.avg_price))} DT`
                      : "—"}
                  </div>
                  <div className="mt-1 text-sm text-ink-500">
                    Average checked price
                  </div>
                </div>
                <div className="p-6">
                  <div className="font-mono text-3xl font-semibold text-ink-950">
                    {stats.top_brands.length}
                  </div>
                  <div className="mt-1 text-sm text-ink-500">
                    Brands covered
                  </div>
                </div>
              </div>

              {stats.top_brands.length > 0 && (
                <div className="mt-6 grid gap-6 sm:grid-cols-2">
                  <div>
                    <div className="mb-4 text-sm font-medium text-ink-950">
                      Most checked brands
                    </div>
                    {stats.top_brands.map((b, i) => (
                      <div
                        key={b.brand}
                        className="mb-2 flex items-center gap-3 text-sm"
                      >
                        <span className="w-4 font-mono text-ink-400">
                          {i + 1}
                        </span>
                        <span className="w-24 truncate text-ink-500">
                          {b.brand.charAt(0).toUpperCase() + b.brand.slice(1)}
                        </span>
                        <div className="h-1.5 flex-1 rounded-full bg-border">
                          <div
                            className="h-full rounded-full bg-amber"
                            style={{
                              width: `${Math.round((b.count / stats.top_brands[0].count) * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="w-8 text-right font-mono text-xs text-ink-500">
                          {b.count}
                        </span>
                      </div>
                    ))}
                  </div>

                  {stats.top_models.length > 0 && (
                    <div>
                      <div className="mb-4 text-sm font-medium text-ink-950">
                        Most checked models
                      </div>
                      {stats.top_models.map((m, i) => (
                        <div
                          key={m.model}
                          className="mb-2 flex items-center gap-3 text-sm"
                        >
                          <span className="w-4 font-mono text-ink-400">
                            {i + 1}
                          </span>
                          <span className="w-24 truncate text-ink-500">
                            {m.model.charAt(0).toUpperCase() + m.model.slice(1)}
                          </span>
                          <div className="h-1.5 flex-1 rounded-full bg-border">
                            <div
                              className="h-full rounded-full bg-steel"
                              style={{
                                width: `${Math.round((m.count / stats.top_models[0].count) * 100)}%`,
                              }}
                            />
                          </div>
                          <span className="w-8 text-right font-mono text-xs text-ink-500">
                            {m.count}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}

        {/* HOW IT WORKS — genuine sequence, so numbering earns its place */}
        <section id="how-it-works" className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-24">
            <h2 className="font-display text-4xl font-bold uppercase tracking-tight text-ink-950">
              How it works
            </h2>

            <div className="relative mt-14">
              <div className="absolute inset-x-0 top-3 hidden border-t-2 border-dashed border-border lg:block" />
              <div className="relative grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
                {HOW_IT_WORKS.map((s) => (
                  <div key={s.step} className="bg-paper pr-6">
                    <div className="mb-4 flex h-7 w-7 items-center justify-center rounded-full border-2 border-steel bg-paper font-mono text-xs font-semibold text-steel">
                      {s.step}
                    </div>
                    <div className="font-semibold text-ink-950">{s.title}</div>
                    <div className="mt-2 text-sm leading-relaxed text-ink-500">
                      {s.desc}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* FEATURES */}
        <section className="border-t bg-steel border-border">
          <div className="mx-auto max-w-6xl px-6 py-24">
            <h2 className="font-display text-4xl font-bold uppercase tracking-tight text-paper">
              Built for the Tunisian market
            </h2>
            <div className="mt-10 grid gap-x-12 gap-y-8 sm:grid-cols-2">
              {FEATURES.map((f) => {
                const Icon = f.icon;
                return (
                  <div
                    key={f.title}
                    className="flex gap-4 border-b border-border pb-8"
                  >
                    <Icon className="mt-1 h-5 w-5 shrink-0 text-amber" />
                    <div>
                      <div className="font-medium text-paper">{f.title}</div>
                      <div className="mt-1 text-sm text-surface-alt">
                        {f.desc}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* UNDER THE HOOD */}
        <section id="under-the-hood" className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-24">
            <div className="grid items-start gap-16 lg:grid-cols-2">
              <div>
                <h2 className="font-display text-4xl font-bold uppercase tracking-tight text-ink-950">
                  How the price is calculated
                </h2>
                <p className="mt-4 max-w-md text-ink-500">
                  Two models split the work: one for budget cars, one for mid
                  and premium cars, combined with a nearest-neighbor search over
                  comparable listings — so a rare or expensive model isn&apos;t
                  dragged toward its brand&apos;s average.
                </p>
                <div className="mt-8 grid grid-cols-2 gap-y-4 border-t border-border pt-6 text-sm">
                  <span className="text-ink-500">Training listings</span>
                  <span className="text-right font-mono text-ink-950">
                    3,373+
                  </span>
                  <span className="text-ink-500">Average error margin</span>
                  <span className="text-right font-mono text-ink-950">
                    ~{avgMape ?? "16.6"}%
                  </span>
                  <span className="text-ink-500">Market</span>
                  <span className="text-right font-mono text-ink-950">
                    Tunisia only
                  </span>
                  <span className="text-ink-500">Price range covered</span>
                  <span className="text-right font-mono text-ink-950">
                    2,500–580,000 DT
                  </span>
                </div>
              </div>

              <div className="rounded-md border-2 border-steel bg-surface p-6">
                {PIPELINE.map((step, i) => (
                  <div key={step}>
                    <div className="rounded border border-border bg-paper px-4 py-3 text-center text-sm text-ink-950">
                      {step}
                    </div>
                    {i < PIPELINE.length - 1 && (
                      <div className="flex justify-center py-1">
                        <div className="h-4 w-0 border-l-2 border-dashed border-steel" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* FINAL CTA — steel band, bookends the header at the top of every page */}
        <section className="bg-steel">
          <div className="mx-auto max-w-6xl px-6 py-24 text-center">
            <h2 className="font-display text-4xl font-bold uppercase tracking-tight text-paper">
              Ready to check a price?
            </h2>
            <p className="mt-3 text-surface-alt">
              Free, instant, no registration required.
            </p>
            <Link
              href="/check"
              className="mt-8 inline-flex items-center gap-2 rounded bg-amber px-6 py-3 text-sm font-medium text-steel transition-colors hover:bg-amber-hover hover:text-paper"
            >
              Check a car price <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
