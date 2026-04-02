# api.py — AutoValu v5
# model_zone encoding + KNN-based range + KNN decides segment

import pickle, json, os, uuid, numpy as np, pandas as pd
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
DB_URL = os.environ.get('DATABASE_URL','postgresql://autovalu:autovalu123@localhost:5432/autovalu')

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id TEXT PRIMARY KEY, timestamp TIMESTAMPTZ DEFAULT NOW(),
            brand TEXT, model TEXT, year INT, fuel TEXT, body_style TEXT,
            car_condition TEXT, trim_level TEXT, mileage_km FLOAT,
            engine_cc FLOAT, seats FLOAT, doors FLOAT, user_price FLOAT,
            predicted_price FLOAT, price_min FLOAT, price_max FLOAT,
            segment TEXT, mileage_assumed BOOLEAN, knn_price FLOAT, knn_dist FLOAT
        );
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY, timestamp TIMESTAMPTZ DEFAULT NOW(),
            brand TEXT, model TEXT, year INT, fuel TEXT, body_style TEXT,
            car_condition TEXT, trim_level TEXT, mileage_km FLOAT,
            engine_cc FLOAT, user_price FLOAT NOT NULL,
            predicted_price FLOAT NOT NULL, segment TEXT,
            status TEXT DEFAULT 'pending', admin_note TEXT
        );
    """)
    conn.commit(); cur.close(); conn.close()
    print("PostgreSQL ready.")

# ── LOAD MODELS ───────────────────────────────────────────────────
print("AutoValu v5 — Loading...")
with open(os.path.join(BASE_DIR,'car_model_budget.pkl'),'rb') as f: model_budget = pickle.load(f)
with open(os.path.join(BASE_DIR,'car_model_mid.pkl'),   'rb') as f: model_mid    = pickle.load(f)
with open(os.path.join(BASE_DIR,'car_encoders.pkl'),    'rb') as f: le_encoders  = pickle.load(f)
with open(os.path.join(BASE_DIR,'car_feature_info.json'),'r',encoding='utf-8') as f: fi = json.load(f)

TARGET_MEAN_FEATURES = fi['target_mean_features']
LABEL_FEATURES       = fi['label_features']
NUM_FEATURES         = fi['num_features']
ALL_FEATURES         = fi['all_features']
NUM_MEDIANS          = fi['num_medians']
BRAND_MEDIANS        = fi['brand_medians']
BRAND_ZONE_MEDIANS   = fi['brand_zone_medians']
MODEL_ZONE_MEDIANS   = fi['model_zone_medians']
PREMIUM_BRANDS       = set(fi['premium_brands'])
B = fi['budget']
M = fi['mid']

print(f"Budget: MAE {B['mae']:,.0f} DT | MAPE {B['mape']:.1f}%")
print(f"Mid   : MAE {M['mae']:,.0f} DT | MAPE {M['mape']:.1f}%")

# ── KNN DATASET ───────────────────────────────────────────────────
DATA_PATH = os.path.join(BASE_DIR, 'data', 'cars_used.csv')
df_knn = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
df_knn['brand']         = df_knn['brand'].str.lower().str.strip()
df_knn['model']         = df_knn['model'].str.lower().str.strip()
df_knn['fuel']          = df_knn['fuel'].str.lower().str.strip()
df_knn['body_style']    = df_knn['body_style'].str.lower().str.strip()
df_knn['car_condition'] = df_knn['car_condition'].str.lower().str.strip()
df_knn['trim_level']    = df_knn['trim_level'].fillna('standard').str.lower().str.strip()
for col in ['year','price','mileage_num','engine_cc_num','seats_num','doors_num','depreciation_zone']:
    df_knn[col] = pd.to_numeric(df_knn[col], errors='coerce')
df_knn_full = df_knn.dropna(subset=['year','price']).copy()
print(f"KNN dataset: {len(df_knn_full)} rows")

try:
    init_db()
except Exception as e:
    print(f"DB WARNING: {e}")

app = FastAPI(title="AutoValu v5", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    brand: str; model: Optional[str]=None; year: int
    fuel: Optional[str]=None; body_style: Optional[str]=None
    car_condition: Optional[str]=None; trim_level: Optional[str]=None
    mileage_km: Optional[float]=None; engine_cc: Optional[float]=None
    user_price: float; predicted_price: float; segment: str

def clean_brand(b):
    return {'mercedes-benz':'mercedes','citroën':'citroen'}.get(b.lower().strip(), b.lower().strip())

def encode_label(col, val):
    le = le_encoders[col]
    v  = str(val).lower().strip()
    if v not in le.classes_: v = 'unknown'
    return float(le.transform([v])[0])

def get_confidence(model_name, brand, seg_fi):
    mc    = seg_fi.get('model_counts', {})
    count = mc.get(str(model_name or '').lower().strip(), 0)
    if count >= 10:
        return {"level":"high","message":"High confidence — based on real listings of this model","color":"green"}
    elif count >= 3:
        return {"level":"medium","message":"Medium confidence — estimated from similar models of this brand","color":"yellow"}
    else:
        return {"level":"low","message":"Low confidence — limited data for this model","color":"orange"}

def get_verdict(user_price, predicted):
    diff = (user_price - predicted) / predicted * 100
    if diff <= -15:
        return {"verdict":"excellent_deal","label":"Excellent deal","color":"green",
                "diff_pct":round(diff,1),"message":f"This price is {abs(diff):.0f}% below market. Great deal.","counter_offer":None}
    elif diff <= 10:
        return {"verdict":"fair_price","label":"Fair price","color":"yellow",
                "diff_pct":round(diff,1),"message":"This price is within the normal market range.","counter_offer":None}
    elif diff <= 25:
        return {"verdict":"expensive","label":"A bit expensive","color":"orange",
                "diff_pct":round(diff,1),"message":f"This price is {diff:.0f}% above market. Try to negotiate.",
                "counter_offer":int(round(predicted*0.94/500)*500)}
    else:
        return {"verdict":"overpriced","label":"Overpriced","color":"red",
                "diff_pct":round(diff,1),"message":f"This price is {diff:.0f}% above market. Walk away or negotiate hard.",
                "counter_offer":int(round(predicted*0.90/500)*500)}

def build_fv(brand, model_name, fuel, body, cond, trim,
             year, car_age, mileage, engine_cc, seats, doors,
             mpy, dep_zone, seg_fi):
    gm = seg_fi['global_mean']
    mc = seg_fi.get('model_counts', {})

    model_zone = f"{model_name}_z{int(dep_zone)}"
    brand_zone = f"{brand}_z{int(dep_zone)}"

    # Hierarchy: model_zone > brand_zone > global_mean
    mz_enc = float(seg_fi['target_means']['model_zone'].get(model_zone,
             seg_fi['target_means']['brand_zone'].get(brand_zone, gm)))
    bz_enc = float(seg_fi['target_means']['brand_zone'].get(brand_zone, gm))
    br_enc = float(seg_fi['target_means']['brand'].get(brand, gm))

    model_freq = float(mc.get(str(model_name or '').lower().strip(), 1.0))

    def num(v, col):
        if v is None: return NUM_MEDIANS.get(col, 0.0)
        try:
            f = float(v)
            return NUM_MEDIANS.get(col, 0.0) if np.isnan(f) else f
        except: return NUM_MEDIANS.get(col, 0.0)

    return np.array([[
        mz_enc, bz_enc, br_enc,
        encode_label('fuel', fuel),
        encode_label('body_style', body),
        encode_label('car_condition', cond),
        encode_label('trim_level', trim),
        float(year), float(car_age), float(mileage),
        num(engine_cc,'engine_cc_num'),
        num(seats,'seats_num'),
        num(doors,'doors_num'),
        float(mpy), float(dep_zone), model_freq,
    ]])

def run_segment(brand, model_name, body, fuel, cond, trim,
                year, car_age, mileage, engine_cc, seats, doors,
                mpy, dep_zone, seg_name):
    seg_fi    = B if seg_name == 'budget' else M
    seg_model = model_budget if seg_name == 'budget' else model_mid
    fv  = build_fv(brand, model_name, fuel, body, cond, trim,
                   year, car_age, mileage, engine_cc, seats, doors,
                   mpy, dep_zone, seg_fi)
    raw  = float(seg_model.predict(fv)[0])
    pred = max(1000.0, round(raw/500)*500)
    conf = get_confidence(model_name, brand, seg_fi)
    return pred, conf, seg_fi['mae'], seg_fi['mape'], seg_fi['training_rows']

def knn_estimate(brand, model_name, year, fuel, body_style, car_condition,
                 trim_level, mileage, engine_cc, seats, doors, dep_zone):
    """
    KNN using ALL user-provided fields.
    Returns (knn_price, best_dist, knn_prices_list) for range calculation.
    """
    try:
        subset = df_knn_full[df_knn_full['brand'] == brand].copy()
        if len(subset) < 2:
            return None, None, []

        model_clean = str(model_name or '').lower().strip()
        fuel_clean  = str(fuel or '').lower().strip()
        body_clean  = str(body_style or '').lower().strip()
        cond_clean  = str(car_condition or '').lower().strip()
        trim_clean  = str(trim_level or 'standard').lower().strip()

        # Distance components
        def model_dist(rm):
            rm = str(rm).lower().strip()
            if rm == model_clean: return 0
            if model_clean and (model_clean in rm or rm in model_clean): return 2
            return 12

        subset = subset.copy()
        subset['d_model']   = subset['model'].apply(model_dist)
        subset['d_year']    = abs(subset['year'].fillna(year) - year)
        subset['d_mile']    = abs(subset['mileage_num'].fillna(mileage) - mileage) / 15000
        subset['d_zone']    = abs(subset['depreciation_zone'].fillna(dep_zone) - dep_zone) * 3

        subset['d_fuel']    = subset['fuel'].apply(
            lambda f: 0 if str(f).lower().strip() == fuel_clean else 3)
        subset['d_body']    = subset['body_style'].apply(
            lambda b: 0 if str(b).lower().strip() == body_clean else 1)
        subset['d_cond']    = subset['car_condition'].apply(
            lambda c: 0 if str(c).lower().strip() == cond_clean else 2)
        subset['d_trim']    = subset['trim_level'].apply(
            lambda t: 0 if str(t).lower().strip() == trim_clean else 1)

        if engine_cc and engine_cc > 0:
            subset['d_cc']  = abs(subset['engine_cc_num'].fillna(engine_cc) - engine_cc) / 300
        else:
            subset['d_cc']  = 0

        subset['d_seats']   = abs(subset['seats_num'].fillna(seats or 5) - (seats or 5))
        subset['d_doors']   = abs(subset['doors_num'].fillna(doors or 4) - (doors or 4))

        subset['total_dist'] = (
            subset['d_model'] * 12.0 +
            subset['d_year']  *  6.0 +
            subset['d_mile']  *  3.0 +
            subset['d_zone']  *  3.0 +
            subset['d_fuel']  *  2.5 +
            subset['d_cond']  *  2.0 +
            subset['d_cc']    *  2.0 +
            subset['d_body']  *  1.5 +
            subset['d_trim']  *  1.0 +
            subset['d_seats'] *  0.5 +
            subset['d_doors'] *  0.5
        )

        closest   = subset.nsmallest(5, 'total_dist')
        best_dist = float(closest['total_dist'].iloc[0])
        weights   = 1.0 / (closest['total_dist'] + 0.1)
        knn_price = float(np.average(closest['price'], weights=weights))
        knn_prices = closest['price'].tolist()

        print(f"\nKNN: {brand} {model_clean} {year} | {int(mileage)}km | {fuel_clean} | {cond_clean}")
        print(closest[['model','year','mileage_num','fuel','car_condition','price','total_dist']].to_string(index=False))
        print(f"KNN: {knn_price:,.0f} DT | best_dist: {best_dist:.1f}")

        return knn_price, best_dist, knn_prices

    except Exception as e:
        print(f"KNN error: {e}")
        return None, None, []

def price_range(predicted, mape):
    """
    Tiered range cap — tighter for expensive cars, wider for cheap ones.
    Reflects real negotiation room in the Tunisian market.
    A 200k Range Rover: ±8% = ±16k (useful)
    A 50k Golf: ±10% = ±5k (useful)
    A 25k Clio: ±12% = ±3k (useful)
    Never uses raw KNN spread — too noisy when fuel/condition varies.
    """
    if predicted >= 100000:
        pct = 0.08
    elif predicted >= 50000:
        pct = 0.10
    else:
        pct = 0.12

    unc  = predicted * pct
    pmin = int(max(1000, round((predicted - unc) / 500) * 500))
    pmax = int(round((predicted + unc) / 500) * 500)
    return pmin, pmax

@app.post("/predict")
def predict(car: CarInput):
    brand      = clean_brand(car.brand)
    year       = int(car.year)
    car_age    = max(1, 2026 - year)
    fuel       = (car.fuel or "gasoline").lower().strip()
    body       = (car.body_style or "sedan").lower().strip()
    cond       = (car.car_condition or "medium").lower().strip()
    trim       = (car.trim_level or "standard").lower().strip()
    engine_cc  = car.engine_cc
    seats      = car.seats
    doors      = car.doors
    model_name = (car.model or '').lower().strip()

    if car.mileage_km is not None:
        mileage, mileage_assumed = float(car.mileage_km), False
    else:
        mileage, mileage_assumed = float(car_age) * 20000.0, True

    mpy = mileage / car_age

    if   car_age <= 3:  dep_zone = 1
    elif car_age <= 8:  dep_zone = 2
    elif car_age <= 15: dep_zone = 3
    else:               dep_zone = 4

    # ── STEP 1: KNN first — get ground truth from real data ───────
    knn_price, best_dist, knn_prices = knn_estimate(
        brand, model_name, year, fuel, body, cond,
        trim, mileage, engine_cc, seats, doors, dep_zone
    )

    # ── STEP 2: Routing — KNN price decides segment ───────────────
    # Use model_zone median as reference when KNN unavailable
    mz_key    = f"{model_name}_z{dep_zone}"
    bz_key    = f"{brand}_z{dep_zone}"
    reference = (knn_price if knn_price
                 else MODEL_ZONE_MEDIANS.get(mz_key,
                      BRAND_ZONE_MEDIANS.get(bz_key,
                      BRAND_MEDIANS.get(brand, 45000.0))))

    if reference >= 85000:
        segment = 'mid'
    elif reference <= 30000:
        segment = 'budget'
    else:
        pred_b, *_ = run_segment(brand, model_name, body, fuel, cond, trim,
                                  year, car_age, mileage, engine_cc, seats,
                                  doors, mpy, dep_zone, 'budget')
        pred_m, *_ = run_segment(brand, model_name, body, fuel, cond, trim,
                                  year, car_age, mileage, engine_cc, seats,
                                  doors, mpy, dep_zone, 'mid')
        segment = 'budget' if abs(pred_b - reference) <= abs(pred_m - reference) else 'mid'

    # ── STEP 3: XGBoost prediction ────────────────────────────────
    xgb_price, confidence, mae, mape, rows = run_segment(
        brand, model_name, body, fuel, cond, trim,
        year, car_age, mileage, engine_cc, seats, doors, mpy, dep_zone, segment
    )

    # ── STEP 4: Blend KNN + XGBoost ──────────────────────────────
    w_knn = 0
    if knn_price is not None and best_dist is not None:
        if best_dist == 0:    w_knn = 0.95
        elif best_dist < 5:   w_knn = 0.85
        elif best_dist < 12:  w_knn = 0.65
        elif best_dist < 20:  w_knn = 0.45
        else:                 w_knn = 0.25

        final_price = (w_knn * knn_price) + ((1 - w_knn) * xgb_price)
        print(f"Blend: XGB={xgb_price:,.0f} KNN={knn_price:,.0f} w_knn={w_knn:.2f} → {final_price:,.0f}")
    else:
        final_price = xgb_price
        print(f"XGBoost only: {final_price:,.0f}")

    predicted = int(max(1000.0, round(final_price / 500) * 500))

    # ── STEP 5: KNN-based range — much tighter than MAPE ─────────
    pmin, pmax = price_range(predicted, mape)

    verdict = get_verdict(car.user_price, predicted) if (car.user_price and car.user_price > 0) else None

    # ── Save to DB ─────────────────────────────────────────────────
    qid = str(uuid.uuid4())[:8]
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO queries
            (id,brand,model,year,fuel,body_style,car_condition,trim_level,
             mileage_km,engine_cc,seats,doors,user_price,predicted_price,
             price_min,price_max,segment,mileage_assumed,knn_price,knn_dist)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (qid,brand,car.model,year,fuel,body,cond,trim,
              car.mileage_km,engine_cc,seats,doors,car.user_price,
              predicted,pmin,pmax,segment,mileage_assumed,knn_price,best_dist))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"DB warning: {e}")

    return {
        "predicted_price": predicted,
        "price_range"    : {"min": pmin, "max": pmax},
        "confidence"     : confidence,
        "verdict"        : verdict,
        "mileage_assumed": mileage_assumed,
        "mileage_used"   : int(round(mileage)),
        "segment"        : segment,
        "model_info"     : {
            "segment"      : segment,
            "training_rows": rows,
            "mae"          : int(round(mae)),
            "mape"         : round(mape, 1),
            "knn_used"     : knn_price is not None,
            "knn_weight"   : round(w_knn, 2),
        }
    }

@app.post("/submit")
def submit_price(data: SubmitInput):
    if data.user_price <= 0: raise HTTPException(400,"Price must be positive")
    if data.user_price > 2000000: raise HTTPException(400,"Price seems unrealistic")
    ratio = data.user_price / max(data.predicted_price, 1)
    if ratio > 5.0 or ratio < 0.2: raise HTTPException(400,"Price too far from estimate")
    sid = str(uuid.uuid4())[:8]
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO submissions
            (id,brand,model,year,fuel,body_style,car_condition,trim_level,
             mileage_km,engine_cc,user_price,predicted_price,segment)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (sid,data.brand,data.model,data.year,data.fuel,data.body_style,
              data.car_condition,data.trim_level,data.mileage_km,data.engine_cc,
              data.user_price,data.predicted_price,data.segment))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")
    return {"success": True, "message": "Thank you."}

ADMIN_SECRET = "autovalu_admin_2026"
ADMIN_USER   = os.environ.get('ADMIN_USERNAME')
ADMIN_PASS   = os.environ.get('ADMIN_PASSWORD')

class LoginInput(BaseModel):
    username: str; password: str

@app.post("/admin/login")
def admin_login(data: LoginInput):
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        return {"success": True, "token": ADMIN_SECRET}
    raise HTTPException(401, "Invalid credentials")

@app.get("/admin/submissions")
def get_submissions(secret: str="", status: str="all"):
    if secret != ADMIN_SECRET: raise HTTPException(403,"Forbidden")
    conn = get_db(); cur = conn.cursor()
    q = "SELECT * FROM submissions ORDER BY timestamp DESC"
    if status != "all": q = "SELECT * FROM submissions WHERE status=%s ORDER BY timestamp DESC"
    cur.execute(q) if status == "all" else cur.execute(q, (status,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/review")
def review_submission(submission_id: str, action: str, secret: str="", note: str=""):
    if secret != ADMIN_SECRET: raise HTTPException(403,"Forbidden")
    if action not in ['approve','reject']: raise HTTPException(400,"approve or reject only")
    status = 'approved' if action == 'approve' else 'rejected'
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE submissions SET status=%s,admin_note=%s WHERE id=%s",(status,note,submission_id))
    if cur.rowcount == 0: raise HTTPException(404,"Not found")
    conn.commit(); cur.close(); conn.close()
    return {"success": True, "action": action, "id": submission_id}

@app.get("/admin/stats")
def get_stats(secret: str=""):
    if secret != ADMIN_SECRET: raise HTTPException(403,"Forbidden")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM queries"); tq = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions"); ts = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='pending'"); tp = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='approved'"); ta = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='rejected'"); tr = cur.fetchone()['c']
    cur.execute("SELECT brand,COUNT(*) as count FROM queries GROUP BY brand ORDER BY count DESC LIMIT 10")
    brands = cur.fetchall(); cur.close(); conn.close()
    return {"total_queries":tq,"submissions":{"total":ts,"pending":tp,"approved":ta,"rejected":tr},
            "top_brands":[dict(r) for r in brands]}

@app.get("/admin/queries")
def get_queries(secret: str="", limit: int=100):
    if secret != ADMIN_SECRET: raise HTTPException(403,"Forbidden")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM queries ORDER BY timestamp DESC LIMIT %s",(limit,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return [dict(r) for r in rows]

@app.get("/stats/public")
def public_stats():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM queries")
        total_checks = cur.fetchone()['c']
        cur.execute("SELECT brand,COUNT(*) as count FROM queries WHERE brand IS NOT NULL AND brand!='' GROUP BY brand ORDER BY count DESC LIMIT 8")
        top_brands = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT model,COUNT(*) as count FROM queries WHERE model IS NOT NULL AND model!='' GROUP BY model ORDER BY count DESC LIMIT 8")
        top_models = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT ROUND(AVG(predicted_price)::numeric,0) as avg FROM queries WHERE predicted_price IS NOT NULL AND predicted_price>0")
        avg_row   = cur.fetchone()
        avg_price = float(avg_row['avg']) if avg_row['avg'] else 0
        cur.close(); conn.close()
        return {"total_checks":total_checks,"top_brands":top_brands,"top_models":top_models,"avg_price":avg_price}
    except:
        return {"total_checks":0,"top_brands":[],"top_models":[],"avg_price":0}

@app.get("/health")
def health():
    return {"status":"ok","version":"5.0.0","segments":{
        "budget":{"mae":int(round(B['mae'])),"mape":round(B['mape'],1),"rows":B['training_rows']},
        "mid"   :{"mae":int(round(M['mae'])),"mape":round(M['mape'],1),"rows":M['training_rows']},
    }}

if __name__ == "__main__":
    import uvicorn
    print("\nAutoValu v5 — model_zone encoding + KNN range")
    print("Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)