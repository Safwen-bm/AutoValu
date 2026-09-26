# training/train_model.py — AutoValu

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import json, pickle, os

# This file sits in backend/training/, so backend/ is one level up.
PROJECT_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE     = os.path.join(PROJECT_ROOT, 'data', 'cars_used.csv')
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'artifacts')
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

print("="*60)
print("AutoValu — model_zone encoding")
print("="*60)

df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
df['brand'] = df['brand'].str.strip().str.lower()
df['model'] = df['model'].str.strip().str.lower()

for col in ['car_age','mileage_num','engine_cc_num','seats_num','doors_num',
            'mileage_per_year','depreciation_zone','price','year']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Clean up leftover columns from old versions
for col in ['model_group','price_segment']:
    if col in df.columns:
        df = df.drop(columns=[col])

df = df[df['price'].notna() & (df['price'] > 500)].copy()
df = df[df['year'].notna()].copy()

print(f"Rows: {len(df)} | Price: {df['price'].min():,.0f}-{df['price'].max():,.0f} DT")

TARGET     = 'price'
BUDGET_MAX = 80000
MID_MIN    = 40000

df_budget = df[df[TARGET] < BUDGET_MAX].copy()
df_mid    = df[df[TARGET] >= MID_MIN].copy()
print(f"Budget: {len(df_budget)} rows | Mid: {len(df_mid)} rows")
print(f"Overlap: {((df[TARGET]>=MID_MIN)&(df[TARGET]<BUDGET_MAX)).sum()} rows")

# ── FEATURE DESIGN ────────────────────────────────────────────────
# model_zone: model + depreciation_zone -> "hilux_z2", "golf 7_z3"
#   Encodes the REAL market price of THIS model at THIS age
# brand_zone: fallback for rare models with < 3 rows
# brand: overall brand signal
# model_freq: how many rows this model has - confidence proxy
# LABEL: fuel, body_style, car_condition, trim_level
# NUM: year, car_age, mileage, cc, seats, doors, mileage_per_year, dep_zone

TARGET_MEAN_FEATURES = ['model_zone', 'brand_zone', 'brand']
LABEL_FEATURES       = ['fuel', 'body_style', 'car_condition', 'trim_level']
NUM_FEATURES         = ['year', 'car_age', 'mileage_num', 'engine_cc_num',
                        'seats_num', 'doors_num', 'mileage_per_year',
                        'depreciation_zone', 'model_freq']
ALL_FEATURES = TARGET_MEAN_FEATURES + LABEL_FEATURES + NUM_FEATURES

def add_zone_features(d):
    d = d.copy()
    dep = d['depreciation_zone'].fillna(2).astype(int).astype(str)
    d['model_zone'] = d['model'] + '_z' + dep
    d['brand_zone'] = d['brand'] + '_z' + dep
    return d

df        = add_zone_features(df)
df_budget = add_zone_features(df_budget)
df_mid    = add_zone_features(df_mid)

# Fit label encoders on full dataset
print("\nFitting encoders...")
le_encoders = {}
df_full = df.copy()
for col in LABEL_FEATURES:
    le = LabelEncoder()
    df_full[col] = df_full[col].fillna('unknown').astype(str).str.strip().str.lower()
    le.fit(df_full[col].tolist() + ['unknown'])
    le_encoders[col] = le
    print(f"  {col:20s}: {len(le.classes_)} values")

# Numeric medians for imputation only
num_medians = {}
for col in NUM_FEATURES:
    if col == 'model_freq':
        num_medians[col] = 5.0
        continue
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        val = df[col].median()
        num_medians[col] = float(val) if pd.notna(val) else 0.0
    else:
        num_medians[col] = 0.0

# Brand and zone medians - for routing in app/inference/predictor.py
brand_median_overall  = df.groupby('brand')[TARGET].median().to_dict()
brand_zone_median_raw = df.groupby(['brand','depreciation_zone'])[TARGET].median()
brand_zone_medians    = {f"{b}_z{int(z)}": float(v)
                         for (b,z),v in brand_zone_median_raw.items()}

# Model zone medians - for routing
model_zone_median_raw = df.groupby(['model','depreciation_zone'])[TARGET].median()
model_zone_medians    = {f"{m}_z{int(z)}": float(v)
                         for (m,z),v in model_zone_median_raw.items()}

premium_brands = [b for b,v in brand_median_overall.items() if v >= 100000]
print(f"\nPremium brands (overall median >= 100k): {sorted(premium_brands)}")

def train_one(df_seg, name, params):
    print(f"\n{'='*60}\nTRAINING: {name} ({len(df_seg)} rows)\n{'='*60}")
    ds = df_seg.copy()

    # Model frequency computed from training data only
    model_counts = ds['model'].value_counts().to_dict()

    for col in LABEL_FEATURES:
        ds[col] = ds[col].fillna('unknown').astype(str).str.strip().str.lower()
        ds[col] = le_encoders[col].transform(
            ds[col].map(lambda x: x if x in le_encoders[col].classes_ else 'unknown')
        )

    for col in NUM_FEATURES:
        if col == 'model_freq':
            ds['model_freq'] = ds['model'].map(model_counts).fillna(1.0)
        elif col in ds.columns:
            ds[col] = pd.to_numeric(ds[col], errors='coerce').fillna(num_medians[col])
        else:
            ds[col] = num_medians[col]

    X_raw = ds[ALL_FEATURES].copy()
    y     = ds[TARGET].copy()

    X_tr_raw, X_te_raw, y_tr, y_te = train_test_split(X_raw, y, test_size=0.2, random_state=42)

    gm = float(y_tr.mean())
    tm = {}
    X_tr = X_tr_raw.copy()
    X_te = X_te_raw.copy()

    for col in TARGET_MEAN_FEATURES:
        t     = pd.DataFrame({'cat': X_tr_raw[col].astype(str), 'price': y_tr.values})
        means = t.groupby('cat')['price'].mean().to_dict()
        X_tr[col] = X_tr_raw[col].astype(str).map(means).fillna(gm)
        X_te[col] = X_te_raw[col].astype(str).map(means).fillna(gm)
        tm[col]   = means
        vals = list(means.values())
        print(f"  {col}: {len(means)} groups | {min(vals):,.0f}-{max(vals):,.0f} DT")

    model = XGBRegressor(**params)
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    print(f"  Trees: {model.best_iteration}")

    yp   = model.predict(X_te)
    mae  = mean_absolute_error(y_te, yp)
    mape = mean_absolute_percentage_error(y_te, yp) * 100
    print(f"  MAE: {mae:,.0f} DT | MAPE: {mape:.1f}%")

    y_arr = np.array(y_te)
    for lo, hi in [(0,30000),(30000,60000),(60000,100000),(100000,9999999)]:
        mask = (y_arr>=lo)&(y_arr<hi)
        if mask.sum() > 3:
            sm = mean_absolute_percentage_error(y_arr[mask], yp[mask])*100
            print(f"    {lo//1000:3d}k-{hi//1000 if hi<9999999 else 'inf':>4}: {sm:.1f}% ({mask.sum()} cars)")

    print("\n  Feature importance:")
    imp = pd.DataFrame({'f': ALL_FEATURES, 'i': model.feature_importances_})
    imp = imp.sort_values('i', ascending=False)
    for _, r in imp.head(10).iterrows():
        print(f"    {r['f']:22s} {r['i']*100:5.1f}%  {'#'*int(r['i']*80)}")

    return model, tm, gm, mae, mape, int(len(X_tr)), model_counts

params_budget = {
    'n_estimators':800, 'learning_rate':0.03, 'max_depth':6,
    'min_child_weight':3, 'subsample':0.8, 'colsample_bytree':0.8,
    'gamma':0.15, 'reg_alpha':0.2, 'reg_lambda':1.5,
    'random_state':42, 'verbosity':0, 'early_stopping_rounds':50,
}
params_mid = {
    'n_estimators':1000, 'learning_rate':0.025, 'max_depth':7,
    'min_child_weight':2, 'subsample':0.85, 'colsample_bytree':0.85,
    'gamma':0.1, 'reg_alpha':0.1, 'reg_lambda':1.0,
    'random_state':42, 'verbosity':0, 'early_stopping_rounds':60,
}

m_b, tm_b, gm_b, mae_b, mape_b, rows_b, mc_b = train_one(df_budget, "Budget (<80k)",  params_budget)
m_m, tm_m, gm_m, mae_m, mape_m, rows_m, mc_m = train_one(df_mid,    "Mid (>=40k)",    params_mid)

print(f"\n{'='*60}\nSAVING to {ARTIFACTS_DIR}\n{'='*60}")
with open(os.path.join(ARTIFACTS_DIR,'car_model_budget.pkl'),'wb') as f: pickle.dump(m_b, f)
with open(os.path.join(ARTIFACTS_DIR,'car_model_mid.pkl'),   'wb') as f: pickle.dump(m_m, f)
with open(os.path.join(ARTIFACTS_DIR,'car_encoders.pkl'),    'wb') as f: pickle.dump(le_encoders, f)

fi = {
    'target_mean_features' : TARGET_MEAN_FEATURES,
    'label_features'       : LABEL_FEATURES,
    'num_features'         : NUM_FEATURES,
    'all_features'         : ALL_FEATURES,
    'num_medians'          : num_medians,
    'budget_max'           : BUDGET_MAX,
    'mid_min'              : MID_MIN,
    'premium_brands'       : premium_brands,
    'brand_medians'        : brand_median_overall,
    'brand_zone_medians'   : brand_zone_medians,
    'model_zone_medians'   : model_zone_medians,
    'label_classes'        : {c: le_encoders[c].classes_.tolist() for c in LABEL_FEATURES},
    'budget': {'target_means':tm_b,'global_mean':gm_b,'mae':float(mae_b),
               'mape':float(mape_b),'training_rows':rows_b,'model_counts':mc_b},
    'mid'   : {'target_means':tm_m,'global_mean':gm_m,'mae':float(mae_m),
               'mape':float(mape_m),'training_rows':rows_m,'model_counts':mc_m},
}
with open(os.path.join(ARTIFACTS_DIR,'car_feature_info.json'),'w',encoding='utf-8') as f:
    json.dump(fi, f, indent=2, ensure_ascii=False)

print("Saved: car_model_budget.pkl")
print("Saved: car_model_mid.pkl")
print("Saved: car_encoders.pkl")
print("Saved: car_feature_info.json")
print(f"\nBudget: MAE {mae_b:,.0f} DT | MAPE {mape_b:.1f}%")
print(f"Mid   : MAE {mae_m:,.0f} DT | MAPE {mape_m:.1f}%")
print("\nNext: from backend/, run `uvicorn app.main:app --reload`")
