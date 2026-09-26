import os
import json
import pickle
import pandas as pd

from app.config import ARTIFACTS_DIR, DATA_DIR

print("AutoValu — loading models...")

with open(os.path.join(ARTIFACTS_DIR, 'car_model_budget.pkl'), 'rb') as f:
    model_budget = pickle.load(f)
with open(os.path.join(ARTIFACTS_DIR, 'car_model_mid.pkl'), 'rb') as f:
    model_mid = pickle.load(f)
with open(os.path.join(ARTIFACTS_DIR, 'car_encoders.pkl'), 'rb') as f:
    le_encoders = pickle.load(f)
with open(os.path.join(ARTIFACTS_DIR, 'car_feature_info.json'), 'r', encoding='utf-8') as f:
    fi = json.load(f)

TARGET_MEAN_FEATURES = fi['target_mean_features']
LABEL_FEATURES       = fi['label_features']
NUM_FEATURES         = fi['num_features']
ALL_FEATURES         = fi['all_features']
NUM_MEDIANS          = fi['num_medians']
BRAND_MEDIANS        = fi['brand_medians']
BRAND_ZONE_MEDIANS   = fi['brand_zone_medians']
MODEL_ZONE_MEDIANS   = fi['model_zone_medians']
PREMIUM_BRANDS       = set(fi['premium_brands'])
BUDGET = fi['budget']
MID    = fi['mid']

print(f"Budget: MAE {BUDGET['mae']:,.0f} DT | MAPE {BUDGET['mape']:.1f}%")
print(f"Mid   : MAE {MID['mae']:,.0f} DT | MAPE {MID['mape']:.1f}%")

# ── KNN reference dataset ────────────────────────────────────────
DATA_PATH = os.path.join(DATA_DIR, 'cars_used.csv')
_df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
_df['brand']         = _df['brand'].str.lower().str.strip()
_df['model']         = _df['model'].str.lower().str.strip()
_df['fuel']          = _df['fuel'].str.lower().str.strip()
_df['body_style']    = _df['body_style'].str.lower().str.strip()
_df['car_condition'] = _df['car_condition'].str.lower().str.strip()
_df['trim_level']    = _df['trim_level'].fillna('standard').str.lower().str.strip()
for col in ['year', 'price', 'mileage_num', 'engine_cc_num', 'seats_num', 'doors_num', 'depreciation_zone']:
    _df[col] = pd.to_numeric(_df[col], errors='coerce')

df_knn_full = _df.dropna(subset=['year', 'price']).copy()
print(f"KNN dataset: {len(df_knn_full)} rows")
