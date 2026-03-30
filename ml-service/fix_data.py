# fix_data.py — AutoValu Data Preparation
# Run this first before train_model.py

import pandas as pd
import numpy as np
import os
import re

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'cars_used_final_combined.csv')
USED_FILE  = os.path.join(BASE_DIR, 'data', 'cars_used.csv')

print("="*60)
print("AutoValu — Data Preparation")
print("="*60)

df = pd.read_csv(INPUT_FILE, sep=',', header=0, encoding='utf-8-sig')
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
print(f"\nRows loaded: {len(df)}")

# ── CLEAN BRAND COLUMN ────────────────────────────────────────────
# Remove rows where brand is garbage (too long, slash, etc.)
df['brand'] = df['brand'].astype(str).str.strip().str.lower()
df = df[df['brand'].str.len() <= 30]
df = df[df['brand'] != '/']
df = df[df['brand'] != 'nan']

# Fix brand name variants
brand_fixes = {
    'mercedes-benz' : 'mercedes',
    'citroën'       : 'citroen',
    'volkswagen.'   : 'volkswagen',
}
for wrong, right in brand_fixes.items():
    df['brand'] = df['brand'].apply(lambda x: right if str(x).startswith(wrong) else x)

print(f"After brand cleaning: {len(df)} rows")
print(f"Unique brands: {df['brand'].nunique()}")

# ── STRIP WHITESPACE ──────────────────────────────────────────────
text_cols = ['brand','model','fuel','engine_cc','body_style',
             'car_condition','trim_level','seats','doors','mileage_km']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
        df[col] = df[col].replace('nan', np.nan)

# ── PARSE NUMBERS ─────────────────────────────────────────────────
def parse_seats(val):
    if pd.isna(val) or str(val).strip() in ['nan','']: return np.nan
    if 'door' in str(val).lower(): return np.nan
    m = re.search(r'(\d+)', str(val))
    if m:
        n = int(m.group(1))
        return float(n) if 1 <= n <= 9 else np.nan
    return np.nan

def parse_doors(val):
    if pd.isna(val) or str(val).strip() in ['nan','']: return np.nan
    m = re.search(r'(\d+)', str(val))
    if m:
        n = int(m.group(1))
        return float(n) if 1 <= n <= 6 else np.nan
    return np.nan

def parse_cc(val):
    s = str(val).strip().lower()
    if s in ['unknown','nan',''] or 'kwh' in s: return np.nan
    try:
        cc = float(s)
        return cc if 500 <= cc <= 9000 else np.nan
    except: return np.nan

def parse_mileage(val):
    s = str(val).strip().lower()
    if s in ['unknown','nan','']: return np.nan
    try:
        km = float(s)
        return km if 0 <= km <= 999999 else np.nan
    except: return np.nan

df['seats_num']     = df['seats'].apply(parse_seats)
df['doors_num']     = df['doors'].apply(parse_doors)
df['engine_cc_num'] = df['engine_cc'].apply(parse_cc)
df['mileage_num']   = df['mileage_km'].apply(parse_mileage)
df['year']          = pd.to_numeric(df['year'], errors='coerce')
df['price']         = pd.to_numeric(df['price'], errors='coerce')

# Remove rows with no price or no year
df = df[df['price'].notna() & df['year'].notna()]
df = df[df['price'] > 500]
print(f"After price/year cleaning: {len(df)} rows")

# ── FEATURE ENGINEERING ───────────────────────────────────────────
df['car_age'] = 2026 - df['year']

df['mileage_per_year'] = np.where(
    (df['mileage_num'].notna()) & (df['car_age'] > 0),
    df['mileage_num'] / df['car_age'], np.nan
)

def dep_zone(age):
    if pd.isna(age): return 2
    if age <= 3:  return 1
    if age <= 8:  return 2
    if age <= 15: return 3
    return 4

df['depreciation_zone'] = df['car_age'].apply(dep_zone)

# ── FILTER: USED CARS ONLY ────────────────────────────────────────
df_used = df[df['condition'] == 'used'].copy().reset_index(drop=True)
print(f"Used cars: {len(df_used)}")

# ── BRAND TIER — computed from actual data ────────────────────────
# This is used by the API for routing, not training
brand_median = df_used.groupby('brand')['price'].median().to_dict()
# Premium brands = median price >= 70k
premium_brands = sorted([b for b, v in brand_median.items() if v >= 70000])
print(f"\nPremium brands (median >= 70k): {premium_brands}")

# ── GROUP RARE MODELS ─────────────────────────────────────────────
model_counts = df_used['model'].value_counts()
rare         = model_counts[model_counts < 5].index.tolist()

def model_group(row):
    if row['model'] in rare:
        body = str(row['body_style']).replace(' ', '_')
        return f"{row['brand']}_{body}"
    return row['model']

df_used['model_group'] = df_used.apply(model_group, axis=1)

print(f"\nModel groups: {df_used['model_group'].nunique()} ({len(rare)} rare models grouped)")

# ── SAVE ──────────────────────────────────────────────────────────
df_used.to_csv(USED_FILE, index=False, encoding='utf-8-sig')

print(f"\n{'='*60}")
print(f"DONE: {len(df_used)} rows saved to cars_used.csv")
print(f"Year range : {df_used['year'].min():.0f}–{df_used['year'].max():.0f}")
print(f"Price range: {df_used['price'].min():,.0f}–{df_used['price'].max():,.0f} DT")
print(f"Brands     : {df_used['brand'].nunique()}")
print(f"\nNext: python train_model.py")