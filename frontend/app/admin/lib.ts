export const API = process.env.NEXT_PUBLIC_ML_URL ?? 'http://localhost:8000';

export type Submission = {
  id: string;
  timestamp: string;
  brand: string;
  model: string;
  year: number;
  fuel: string;
  body_style: string;
  car_condition: string;
  trim_level: string;
  mileage_km: number | null;
  engine_cc: number | null;
  user_price: number;
  predicted_price: number;
  segment: string;
  status: string;
  admin_note: string | null;
};

export type Stats = {
  total_queries: number;
  submissions: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  top_brands: { brand: string; count: number }[];
};

export const fmt = (n: number) => n?.toLocaleString('fr-TN') + ' DT';

export const diffPct = (user: number, pred: number) => {
  const d = ((user - pred) / pred) * 100;
  return `${d > 0 ? '+' : ''}${d.toFixed(1)}%`;
};

// Reuses the site-wide verdict palette so "great/fair/steep/bad" means the
// same thing here as it does on the public price checker.
export const diffColorClass = (user: number, pred: number) => {
  const d = ((user - pred) / pred) * 100;
  if (d <= -15) return 'text-verdict-great';
  if (d <= 10) return 'text-amber';
  if (d <= 25) return 'text-verdict-steep';
  return 'text-verdict-bad';
};