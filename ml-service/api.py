# api.py — AutoValu Car Price Intelligence API v3
# WHERE: deals-analyzer\ml-service\api.py
# HOW TO RUN: python api.py
# Docs: http://localhost:8000/docs

import pickle, json, os, uuid, numpy as np, pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── DATABASE ──────────────────────────────────────────────────────
DB_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://autovalu:autovalu123@localhost:5432/autovalu'
)

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id              TEXT PRIMARY KEY,
            timestamp       TIMESTAMPTZ DEFAULT NOW(),
            brand           TEXT, model TEXT, year INT,
            fuel            TEXT, body_style TEXT, car_condition TEXT,
            trim_level      TEXT, mileage_km FLOAT, engine_cc FLOAT,
            seats           FLOAT, doors FLOAT, user_price FLOAT,
            predicted_price FLOAT, price_min FLOAT, price_max FLOAT,
            segment         TEXT, mileage_assumed BOOLEAN,
            knn_price       FLOAT, knn_dist FLOAT
        );
        CREATE TABLE IF NOT EXISTS submissions (
            id              TEXT PRIMARY KEY,
            timestamp       TIMESTAMPTZ DEFAULT NOW(),
            brand           TEXT, model TEXT, year INT,
            fuel            TEXT, body_style TEXT, car_condition TEXT,
            trim_level      TEXT, mileage_km FLOAT, engine_cc FLOAT,
            user_price      FLOAT NOT NULL,
            predicted_price FLOAT NOT NULL,
            segment         TEXT,
            status          TEXT DEFAULT 'pending',
            admin_note      TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("PostgreSQL connected and tables ready.")

# ── LOAD MODELS ───────────────────────────────────────────────────
print("AutoValu v3 — Loading models...")
with open(os.path.join(BASE_DIR,'car_model_budget.pkl'), 'rb') as f: model_budget = pickle.load(f)
with open(os.path.join(BASE_DIR,'car_model_mid.pkl'),    'rb') as f: model_mid    = pickle.load(f)
with open(os.path.join(BASE_DIR,'car_encoders.pkl'),     'rb') as f: le_encoders  = pickle.load(f)
with open(os.path.join(BASE_DIR,'car_feature_info.json'),'r', encoding='utf-8') as f: fi = json.load(f)

TARGET_MEAN_FEATURES = fi['target_mean_features']
LABEL_FEATURES       = fi['label_features']
NUM_FEATURES         = fi['num_features']
ALL_FEATURES         = fi['all_features']
NUM_MEDIANS          = fi['num_medians']
BUDGET_MAX           = fi['budget_max']
MID_MIN              = fi['mid_min']
BRAND_MEDIANS        = fi['brand_medians']
B = fi['budget']
M = fi['mid']

print(f"Budget : MAE {B['mae']:,.0f} DT | MAPE {B['mape']:.1f}%")
print(f"Mid    : MAE {M['mae']:,.0f} DT | MAPE {M['mape']:.1f}%")

# ── LOAD KNN DATASET ──────────────────────────────────────────────
# Use the already-parsed columns (mileage_num, engine_cc_num)
# so we keep maximum rows and don't lose old cars
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'cars_used.csv')
df_knn = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
df_knn['brand'] = df_knn['brand'].str.lower().str.strip()
df_knn['model'] = df_knn['model'].str.lower().str.strip()
df_knn['year']  = pd.to_numeric(df_knn['year'],  errors='coerce')
df_knn['price'] = pd.to_numeric(df_knn['price'], errors='coerce')
# Use mileage_num (already parsed) — not the raw mileage_km string
df_knn['mileage_num']    = pd.to_numeric(df_knn['mileage_num'],    errors='coerce')
df_knn['engine_cc_num']  = pd.to_numeric(df_knn['engine_cc_num'],  errors='coerce')
# KNN only needs rows where we know mileage AND engine AND price
df_knn_full = df_knn.dropna(subset=['year','mileage_num','price']).copy()
print(f"KNN dataset: {len(df_knn_full)} rows (mileage known)")

# Connect to DB
try:
    init_db()
except Exception as e:
    print(f"DB WARNING: {e} — running without database")

# ── APP ───────────────────────────────────────────────────────────
app = FastAPI(title="AutoValu v3", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── SCHEMAS ───────────────────────────────────────────────────────
class CarInput(BaseModel):
    brand        : str
    model        : Optional[str]   = None
    year         : int
    fuel         : Optional[str]   = "gasoline"
    body_style   : Optional[str]   = None
    car_condition: Optional[str]   = "medium"
    trim_level   : Optional[str]   = "standard"
    mileage_km   : Optional[float] = None
    engine_cc    : Optional[float] = None
    seats        : Optional[float] = None
    doors        : Optional[float] = None
    user_price   : Optional[float] = None

class SubmitInput(BaseModel):
    brand          : str
    model          : Optional[str]   = None
    year           : int
    fuel           : Optional[str]   = None
    body_style     : Optional[str]   = None
    car_condition  : Optional[str]   = None
    trim_level     : Optional[str]   = None
    mileage_km     : Optional[float] = None
    engine_cc      : Optional[float] = None
    user_price     : float
    predicted_price: float
    segment        : str

# ── HELPERS ───────────────────────────────────────────────────────
def clean_brand(b: str) -> str:
    b = b.lower().strip()
    return {'mercedes-benz':'mercedes','citroën':'citroen'}.get(b, b)

def resolve_model_group(brand, model, body_style, seg_fi):
    mg = seg_fi['target_means']['model_group']
    if model:
        c = model.lower().strip()
        if c in mg: return c
        for k in mg:
            if c.startswith(k) or k.startswith(c): return k
    if body_style:
        fb = f"{brand}_{body_style.lower().strip().replace(' ','_')}"
        if fb in mg: return fb
    return f"{brand}_sedan"

def get_confidence(mg, brand, seg_fi):
    bk = brand in seg_fi['target_means']['brand']
    mk = mg in seg_fi['target_means']['model_group']
    ig = any(mg == f"{b}_{s}" for b in seg_fi['target_means']['brand']
             for s in ['sedan','hatchback','suv_4x2','suv_4x4','pickup_4x4','pickup_4x2',
                       'crossover','wagon','mpv','light_commercial','heavy_commercial',
                       'coupe','convertible'])
    if mk and not ig:
        return {"level":"high",   "message":"High confidence — based on real listings of this model",       "color":"green"}
    elif bk:
        return {"level":"medium", "message":"Medium confidence — estimated from similar models of this brand","color":"yellow"}
    else:
        return {"level":"low",    "message":"Low confidence — limited data for this brand",                  "color":"orange"}

def get_verdict(user_price, predicted):
    diff = (user_price - predicted) / predicted * 100
    if diff <= -15:
        return {"verdict":"excellent_deal","label":"Excellent deal","color":"green",
                "diff_pct":round(diff,1),
                "message":f"This price is {abs(diff):.0f}% below market. Great deal.",
                "counter_offer":None}
    elif diff <= 10:
        return {"verdict":"fair_price","label":"Fair price","color":"yellow",
                "diff_pct":round(diff,1),
                "message":"This price is within the normal market range.",
                "counter_offer":None}
    elif diff <= 25:
        return {"verdict":"expensive","label":"A bit expensive","color":"orange",
                "diff_pct":round(diff,1),
                "message":f"This price is {diff:.0f}% above market. Try to negotiate.",
                "counter_offer":int(round(predicted*0.94/500)*500)}
    else:
        return {"verdict":"overpriced","label":"Overpriced","color":"red",
                "diff_pct":round(diff,1),
                "message":f"This price is {diff:.0f}% above market. Walk away or negotiate hard.",
                "counter_offer":int(round(predicted*0.90/500)*500)}

def encode_label(col, val):
    le = le_encoders[col]
    v  = str(val).lower().strip()
    if v not in le.classes_: v = 'unknown'
    return float(le.transform([v])[0])

def build_fv(brand, mg, fuel, body, cond, trim, car_age, mileage,
             engine_cc, seats, doors, mpy, dep_zone, seg_fi):
    def num(v, col): return float(v) if v is not None else NUM_MEDIANS.get(col, 0.0)
    gm = seg_fi['global_mean']
    return np.array([[
        float(seg_fi['target_means']['brand'].get(brand, gm)),
        float(seg_fi['target_means']['model_group'].get(mg, gm)),
        encode_label('fuel', fuel),
        encode_label('body_style', body),
        encode_label('car_condition', cond),
        encode_label('trim_level', trim),
        float(car_age), float(mileage),
        num(engine_cc,'engine_cc_num'),
        num(seats,'seats_num'),
        num(doors,'doors_num'),
        float(mpy), float(dep_zone),
    ]])

def run_segment(brand, model_name, body, fuel, cond, trim,
                car_age, mileage, engine_cc, seats, doors,
                mpy, dep_zone, seg_name):
    seg_fi    = B if seg_name == 'budget' else M
    seg_model = model_budget if seg_name == 'budget' else model_mid
    mg  = resolve_model_group(brand, model_name, body, seg_fi)
    fv  = build_fv(brand, mg, fuel, body, cond, trim,
                   car_age, mileage, engine_cc, seats, doors, mpy, dep_zone, seg_fi)
    raw  = float(seg_model.predict(fv)[0])
    pred = max(1000.0, round(raw / 500) * 500)
    conf = get_confidence(mg, brand, seg_fi)
    return pred, conf, mg, seg_fi['mae'], seg_fi['mape'], seg_fi['training_rows']

def knn_price_estimate(brand, model_name, year, mileage, engine_cc):
    """
    Find the 5 most similar real cars and return weighted average price.
    Uses mileage_num (pre-parsed) to keep maximum rows.
    Returns (price, best_distance) or (None, None) if no match.
    """
    try:
        subset = df_knn_full[df_knn_full['brand'] == brand].copy()
        if len(subset) < 2:
            return None, None

        # Model match score — reward exact model matches
        mg_clean = str(model_name or '').lower().strip()
        def model_score(row_model):
            rm = str(row_model).lower().strip()
            if rm == mg_clean:   return 0    # exact match
            if mg_clean in rm or rm in mg_clean: return 1   # partial match
            return 8             # different model — heavy penalty

        subset = subset.copy()
        subset['model_score'] = subset['model_group'].apply(model_score)
        subset['year_diff']   = abs(subset['year'] - year)
        # 20,000 km difference = 1 unit distance
        subset['mile_diff']   = abs(subset['mileage_num'] - mileage) / 20000
        # 200cc difference = 1 unit distance (0 if engine unknown)
        if engine_cc and engine_cc > 0:
            subset['cc_diff'] = abs(subset['engine_cc_num'].fillna(engine_cc) - engine_cc) / 200
        else:
            subset['cc_diff'] = 0

        subset['total_dist'] = (
            subset['model_score'] * 15.0 +
            subset['year_diff']   *  6.0 +
            subset['mile_diff']   *  3.0 +
            subset['cc_diff']     *  2.0
        )

        closest = subset.nsmallest(5, 'total_dist')
        best_dist = float(closest['total_dist'].iloc[0])

        # Weighted average — closer cars get more weight
        weights    = 1.0 / (closest['total_dist'] + 0.1)
        knn_price  = float(np.average(closest['price'], weights=weights))

        print(f"\nKNN: {brand} {mg_clean} {year} | {int(mileage)}km")
        print(closest[['model','year','mileage_num','price','total_dist']].to_string(index=False))
        print(f"KNN estimate: {knn_price:,.0f} DT | best dist: {best_dist:.1f}")

        return knn_price, best_dist

    except Exception as e:
        print(f"KNN error: {e}")
        return None, None

# ── PREDICT ───────────────────────────────────────────────────────
@app.post("/predict")
def predict(car: CarInput):
    brand = clean_brand(car.brand)
    year  = int(car.year)
    car_age   = max(1, 2026 - year)
    fuel      = (car.fuel or "gasoline").lower().strip()
    body      = (car.body_style or "sedan").lower().strip()
    cond      = (car.car_condition or "medium").lower().strip()
    trim      = (car.trim_level or "standard").lower().strip()
    engine_cc = car.engine_cc
    seats     = car.seats
    doors     = car.doors

    if car.mileage_km is not None:
        mileage, mileage_assumed = float(car.mileage_km), False
    else:
        mileage, mileage_assumed = float(car_age) * 20000.0, True

    mpy = mileage / car_age

    if   car_age <= 3:  dep_zone = 1
    elif car_age <= 8:  dep_zone = 2
    elif car_age <= 15: dep_zone = 3
    else:               dep_zone = 4

    # ── ROUTING by brand median ────────────────────────────────────
    brand_med = BRAND_MEDIANS.get(brand, 45000.0)

    if brand_med >= 100000:
        segment = 'mid'
    elif brand_med < 35000:
        segment = 'budget'
    else:
        pred_b, *_ = run_segment(brand, car.model, body, fuel, cond, trim,
                                  car_age, mileage, engine_cc, seats, doors, mpy, dep_zone, 'budget')
        pred_m, *_ = run_segment(brand, car.model, body, fuel, cond, trim,
                                  car_age, mileage, engine_cc, seats, doors, mpy, dep_zone, 'mid')
        age_factor = max(0.3, 1.0 - (car_age * 0.035))
        expected   = brand_med * age_factor
        segment    = 'budget' if abs(pred_b - expected) <= abs(pred_m - expected) else 'mid'

    # ── XGBoost prediction ─────────────────────────────────────────
    xgb_price, confidence, model_group, mae, mape, rows = run_segment(
        brand, car.model, body, fuel, cond, trim,
        car_age, mileage, engine_cc, seats, doors, mpy, dep_zone, segment
    )

    # ── KNN blend ──────────────────────────────────────────────────
    # Your logic: close match → trust KNN, loose match → trust XGBoost
    knn_price, best_dist = knn_price_estimate(
        brand, car.model, year, mileage, engine_cc
    )

    if knn_price is not None and best_dist is not None:
        if best_dist < 5.0:
            w_knn = 0.8   # near-twin found — trust KNN heavily
        elif best_dist < 10.0:
            w_knn = 0.5   # good match — 50/50
        else:
            w_knn = 0.2   # loose match — trust XGBoost more

        final_price = (w_knn * knn_price) + ((1 - w_knn) * xgb_price)
        print(f"Blend: XGB={xgb_price:,.0f} KNN={knn_price:,.0f} w_knn={w_knn} → {final_price:,.0f}")
    else:
        final_price = xgb_price
        print(f"XGBoost only (no KNN match): {final_price:,.0f}")

    predicted = int(max(1000.0, round(final_price / 500) * 500))

    # Range based on final predicted price (not pre-blend)
    unc   = predicted * (mape / 100)
    pmin  = int(max(1000.0, round((predicted - unc) / 500) * 500))
    pmax  = int(round((predicted + unc) / 500) * 500)

    verdict = get_verdict(car.user_price, predicted) if (car.user_price and car.user_price > 0) else None

    # ── Save to DB ─────────────────────────────────────────────────
    qid = str(uuid.uuid4())[:8]
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO queries
            (id,brand,model,year,fuel,body_style,car_condition,trim_level,
             mileage_km,engine_cc,seats,doors,user_price,predicted_price,
             price_min,price_max,segment,mileage_assumed,knn_price,knn_dist)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (qid, brand, car.model, year, fuel, body, cond, trim,
              car.mileage_km, engine_cc, seats, doors, car.user_price,
              predicted, pmin, pmax, segment, mileage_assumed,
              knn_price, best_dist))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB save warning: {e}")

    return {
        "predicted_price": predicted,
        "price_range"    : {"min": pmin, "max": pmax},
        "confidence"     : confidence,
        "verdict"        : verdict,
        "mileage_assumed": mileage_assumed,
        "mileage_used"   : int(round(mileage)),
        "segment"        : segment,
        "model_info"     : {
            "model_group"  : model_group,
            "segment"      : segment,
            "training_rows": rows,
            "mae"          : int(round(mae)),
            "mape"         : round(mape, 1),
            "knn_used"     : knn_price is not None,
        }
    }

# ── SUBMIT ────────────────────────────────────────────────────────
@app.post("/submit")
def submit_price(data: SubmitInput):
    if data.user_price <= 0:
        raise HTTPException(400, "Price must be positive")
    if data.user_price > 2000000:
        raise HTTPException(400, "Price seems unrealistic")
    ratio = data.user_price / max(data.predicted_price, 1)
    if ratio > 5.0 or ratio < 0.2:
        raise HTTPException(400, "Price is too far from our estimate — please double check")

    sid = str(uuid.uuid4())[:8]
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO submissions
            (id,brand,model,year,fuel,body_style,car_condition,trim_level,
             mileage_km,engine_cc,user_price,predicted_price,segment)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (sid, data.brand, data.model, data.year, data.fuel,
              data.body_style, data.car_condition, data.trim_level,
              data.mileage_km, data.engine_cc,
              data.user_price, data.predicted_price, data.segment))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")

    return {"success": True, "message": "Thank you. Your submission will help improve predictions."}

# ── ADMIN ─────────────────────────────────────────────────────────
ADMIN_SECRET = "autovalu_admin_2026"
ADMIN_USER = os.environ.get('ADMIN_USERNAME')
ADMIN_PASS = os.environ.get('ADMIN_PASSWORD')

class LoginInput(BaseModel):
    username: str
    password: str

@app.post("/admin/login")
def admin_login(data: LoginInput):
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        return {"success": True, "token": ADMIN_SECRET}
    raise HTTPException(401, "Invalid credentials")

@app.get("/admin/submissions")
def get_submissions(secret: str = "", status: str = "all"):
    if secret != ADMIN_SECRET: raise HTTPException(403, "Forbidden")
    conn = get_db()
    cur  = conn.cursor()
    if status == "all":
        cur.execute("SELECT * FROM submissions ORDER BY timestamp DESC")
    else:
        cur.execute("SELECT * FROM submissions WHERE status=%s ORDER BY timestamp DESC", (status,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/review")
def review_submission(submission_id: str, action: str, secret: str = "", note: str = ""):
    if secret != ADMIN_SECRET: raise HTTPException(403, "Forbidden")
    if action not in ['approve','reject']: raise HTTPException(400, "approve or reject only")
    status = 'approved' if action == 'approve' else 'rejected'
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("UPDATE submissions SET status=%s, admin_note=%s WHERE id=%s", (status, note, submission_id))
    if cur.rowcount == 0: raise HTTPException(404, "Not found")
    conn.commit(); cur.close(); conn.close()
    return {"success": True, "action": action, "id": submission_id}

@app.get("/admin/stats")
def get_stats(secret: str = ""):
    if secret != ADMIN_SECRET: raise HTTPException(403, "Forbidden")
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM queries"); tq = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions"); ts = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='pending'"); tp = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='approved'"); ta = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='rejected'"); tr = cur.fetchone()['c']
    cur.execute("SELECT brand, COUNT(*) as count FROM queries GROUP BY brand ORDER BY count DESC LIMIT 10")
    brands = cur.fetchall()
    cur.close(); conn.close()
    return {
        "total_queries": tq,
        "submissions"  : {"total":ts,"pending":tp,"approved":ta,"rejected":tr},
        "top_brands"   : [dict(r) for r in brands],
    }

@app.get("/admin/queries")
def get_queries(secret: str = "", limit: int = 100):
    if secret != ADMIN_SECRET: raise HTTPException(403, "Forbidden")
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM queries ORDER BY timestamp DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [dict(r) for r in rows]

@app.get("/stats/public")
def public_stats():
    """Public stats for the landing page — no sensitive data."""
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) as c FROM queries")
        total_checks = cur.fetchone()['c']

        cur.execute("""
            SELECT brand, COUNT(*) as count
            FROM queries
            WHERE brand IS NOT NULL AND brand != ''
            GROUP BY brand
            ORDER BY count DESC
            LIMIT 8
        """)
        top_brands = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT model, COUNT(*) as count
            FROM queries
            WHERE model IS NOT NULL AND model != ''
            GROUP BY model
            ORDER BY count DESC
            LIMIT 8
        """)
        top_models = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT segment, COUNT(*) as count
            FROM queries
            WHERE segment IS NOT NULL
            GROUP BY segment
        """)
        segments = {r['segment']: r['count'] for r in cur.fetchall()}

        cur.execute("""
            SELECT ROUND(AVG(predicted_price)::numeric, 0) as avg
            FROM queries
            WHERE predicted_price IS NOT NULL AND predicted_price > 0
        """)
        avg_row = cur.fetchone()
        avg_price = float(avg_row['avg']) if avg_row['avg'] else 0

        cur.close()
        conn.close()

        return {
            "total_checks": total_checks,
            "top_brands"  : top_brands,
            "top_models"  : top_models,
            "segments"    : segments,
            "avg_price"   : avg_price,
        }
    except Exception as e:
        return {
            "total_checks": 0,
            "top_brands"  : [],
            "top_models"  : [],
            "segments"    : {},
            "avg_price"   : 0,
        }

@app.get("/health")
def health():
    return {"status":"ok","version":"3.0.0","segments":{
        "budget": {"mae":int(round(B['mae'])),"mape":round(B['mape'],1),"rows":B['training_rows']},
        "mid"   : {"mae":int(round(M['mae'])),"mape":round(M['mape'],1),"rows":M['training_rows']},
    }}

if __name__ == "__main__":
    import uvicorn
    print("\nAutoValu API v3 — XGBoost + KNN + PostgreSQL")
    print("Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)