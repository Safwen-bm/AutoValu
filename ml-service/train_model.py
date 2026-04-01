# train_model.py — AutoValu Two-Segment Training
# Segments split by PRICE with overlapping ranges to avoid boundary problems

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import json, pickle, os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'cars_used.csv')

print("="*60)
print("AutoValu — Training Two-Segment XGBoost")
print("="*60)

df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
df['brand'] = df['brand'].str.strip().str.lower()

# Force numeric columns to be numeric — CSV sometimes saves them as strings
for col in ['car_age', 'mileage_num', 'engine_cc_num', 'seats_num',
            'doors_num', 'mileage_per_year', 'depreciation_zone',
            'price', 'year']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"\nRows: {len(df)} | Price: {df['price'].min():,.0f}–{df['price'].max():,.0f} DT")

TARGET = 'price'

# Overlapping segments — cars between 40k-80k train in BOTH models
# This prevents the sharp boundary problem
BUDGET_MAX  = 80000   # budget model trains on cars < 80k
MID_MIN     = 40000   # mid model trains on cars >= 40k

df_budget = df[df[TARGET] < BUDGET_MAX].copy()
df_mid    = df[df[TARGET] >= MID_MIN].copy()

print(f"Budget model trains on : {len(df_budget)} rows (< 80k DT)")
print(f"Mid model trains on    : {len(df_mid)} rows (>= 40k DT)")
print(f"Overlap zone           : {((df[TARGET]>=MID_MIN)&(df[TARGET]<BUDGET_MAX)).sum()} rows (40-80k)")

TARGET_MEAN_FEATURES = ['brand', 'model_group']
LABEL_FEATURES       = ['fuel', 'body_style', 'car_condition', 'trim_level']
NUM_FEATURES         = ['car_age', 'mileage_num', 'engine_cc_num',
                         'seats_num', 'doors_num', 'mileage_per_year', 'depreciation_zone']
ALL_FEATURES = TARGET_MEAN_FEATURES + LABEL_FEATURES + NUM_FEATURES

# Fit encoders on FULL dataset so both models understand all values
print("\nFitting encoders on full dataset...")
le_encoders = {}
df_full = df.copy()
df_full['trim_level'] = df_full['trim_level'].fillna('standard').astype(str).str.strip()
for col in LABEL_FEATURES:
    le = LabelEncoder()
    df_full[col] = df_full[col].fillna('unknown').astype(str).str.strip()
    le.fit(df_full[col].tolist() + ['unknown'])
    le_encoders[col] = le
    print(f"  {col:20s}: {len(le.classes_)} values")

# Medians from full dataset
# Force all numerical columns to numeric type first
# (some columns may have been saved as strings after CSV export)
for col in NUM_FEATURES:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

num_medians = {}
for col in NUM_FEATURES:
    m = df[col].median() if col in df.columns else 0.0
    num_medians[col] = float(m) if not np.isnan(float(m) if m is not None else float('nan')) else 0.0

print("\nMedians:")
for k, v in num_medians.items():
    print(f"  {k:22s}: {v:,.0f}")

# Brand tier for routing (computed from data, not hardcoded)
brand_median = df.groupby('brand')[TARGET].median().to_dict()
premium_brands = [b for b, v in brand_median.items() if v >= 70000]
print(f"\nPremium brands (median >= 70k): {sorted(premium_brands)}")

def train_one(df_seg, name, params):
    print(f"\n{'='*60}")
    print(f"TRAINING: {name} ({len(df_seg)} rows)")
    print(f"{'='*60}")

    ds = df_seg.copy()
    ds['trim_level'] = ds['trim_level'].fillna('standard').astype(str).str.strip()
    for col in LABEL_FEATURES:
        ds[col] = ds[col].fillna('unknown').astype(str).str.strip()
        ds[col] = le_encoders[col].transform(
            ds[col].map(lambda x: x if x in le_encoders[col].classes_ else 'unknown')
        )
    for col in NUM_FEATURES:
        ds[col] = ds[col].fillna(num_medians[col]) if col in ds.columns else num_medians[col]

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
        print(f"  {col}: {len(means)} categories, {min(means.values()):,.0f}–{max(means.values()):,.0f} DT")

    m = XGBRegressor(**params)
    m.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    print(f"  Trees used: {m.best_iteration}")

    yp   = m.predict(X_te)
    mae  = mean_absolute_error(y_te, yp)
    mape = mean_absolute_percentage_error(y_te, yp) * 100
    print(f"  MAE: {mae:,.0f} DT | MAPE: {mape:.1f}%")

    # Show by price bracket
    y_arr = np.array(y_te)
    for lo, hi in [(0,30000),(30000,60000),(60000,100000),(100000,9999999)]:
        mask = (y_arr>=lo)&(y_arr<hi)
        if mask.sum() > 3:
            seg_mape = mean_absolute_percentage_error(y_arr[mask], yp[mask])*100
            print(f"    {lo//1000:3d}k–{hi//1000 if hi<9999999 else '∞':>3}: {seg_mape:.1f}% ({mask.sum()} cars)")

    print(f"\n  Samples:")
    rng = np.random.default_rng(42)
    idx = rng.choice(len(y_arr), min(10, len(y_arr)), replace=False)
    for i in idx:
        a, p = y_arr[i], yp[i]
        pct  = abs(p-a)/a*100
        flag = " ⚠" if pct>30 else ""
        print(f"    {a:>10,.0f} → {p:>10,.0f}  ({pct:.0f}%{flag})")

    print(f"\n  Feature importance:")
    imp = pd.DataFrame({'f': ALL_FEATURES, 'i': m.feature_importances_}).sort_values('i', ascending=False)
    for _, r in imp.head(8).iterrows():
        print(f"    {r['f']:22s} {r['i']*100:5.1f}%  {'█'*int(r['i']*80)}")

    return m, tm, gm, mae, mape, int(len(X_tr))

params_budget = {
    'n_estimators':600, 'learning_rate':0.04, 'max_depth':6,
    'min_child_weight':3, 'subsample':0.8, 'colsample_bytree':0.8,
    'gamma':0.2, 'reg_alpha':0.2, 'reg_lambda':1.5,
    'random_state':42, 'verbosity':0, 'early_stopping_rounds':40,
}
params_mid = {
    'n_estimators':800, 'learning_rate':0.04, 'max_depth':7,
    'min_child_weight':2, 'subsample':0.85, 'colsample_bytree':0.85,
    'gamma':0.1, 'reg_alpha':0.1, 'reg_lambda':1.0,
    'random_state':42, 'verbosity':0, 'early_stopping_rounds':50,
}

m_b, tm_b, gm_b, mae_b, mape_b, rows_b = train_one(df_budget, "Budget  (<  80k DT)", params_budget)
m_m, tm_m, gm_m, mae_m, mape_m, rows_m = train_one(df_mid,    "Mid     (>= 40k DT)", params_mid)

print(f"\n{'='*60}\nSAVING\n{'='*60}")
with open(os.path.join(BASE_DIR,'car_model_budget.pkl'), 'wb') as f: pickle.dump(m_b, f)
with open(os.path.join(BASE_DIR,'car_model_mid.pkl'),    'wb') as f: pickle.dump(m_m, f)
with open(os.path.join(BASE_DIR,'car_encoders.pkl'),     'wb') as f: pickle.dump(le_encoders, f)

fi = {
    'target_mean_features': TARGET_MEAN_FEATURES,
    'label_features'      : LABEL_FEATURES,
    'num_features'        : NUM_FEATURES,
    'all_features'        : ALL_FEATURES,
    'num_medians'         : num_medians,
    'budget_max'          : BUDGET_MAX,
    'mid_min'             : MID_MIN,
    'premium_brands'      : premium_brands,
    'brand_medians'       : {k: float(v) for k, v in brand_median.items()},
    'label_classes'       : {c: le_encoders[c].classes_.tolist() for c in LABEL_FEATURES},
    'budget': {'target_means':tm_b,'global_mean':gm_b,'mae':float(mae_b),'mape':float(mape_b),'training_rows':rows_b},
    'mid'   : {'target_means':tm_m,'global_mean':gm_m,'mae':float(mae_m),'mape':float(mape_m),'training_rows':rows_m},
}
with open(os.path.join(BASE_DIR,'car_feature_info.json'),'w',encoding='utf-8') as f:
    json.dump(fi, f, indent=2, ensure_ascii=False)

print("✅ car_model_budget.pkl")
print("✅ car_model_mid.pkl")
print("✅ car_encoders.pkl")
print("✅ car_feature_info.json")
print(f"\nBudget : MAE {mae_b:,.0f} DT | MAPE {mape_b:.1f}%")
print(f"Mid    : MAE {mae_m:,.0f} DT | MAPE {mape_m:.1f}%")
print("\nNext: python api.py")