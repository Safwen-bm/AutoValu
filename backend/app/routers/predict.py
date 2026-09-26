import uuid
from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.schemas import CarInput, SubmitInput
from app.inference.pricing import clean_brand, get_verdict, price_range
from app.inference.predictor import run_segment
from app.inference.knn import knn_estimate
from app.inference.loader import MODEL_ZONE_MEDIANS, BRAND_ZONE_MEDIANS, BRAND_MEDIANS

router = APIRouter()


@router.post("/predict")
def predict(car: CarInput):
    brand = clean_brand(car.brand)
    year = int(car.year)
    car_age = max(1, 2026 - year)
    fuel = (car.fuel or "gasoline").lower().strip()
    body = (car.body_style or "sedan").lower().strip()
    cond = (car.car_condition or "medium").lower().strip()
    trim = (car.trim_level or "standard").lower().strip()
    engine_cc = car.engine_cc
    seats = car.seats
    doors = car.doors
    model_name = (car.model or '').lower().strip()

    if car.mileage_km is not None:
        mileage, mileage_assumed = float(car.mileage_km), False
    else:
        mileage, mileage_assumed = float(car_age) * 20000.0, True

    mpy = mileage / car_age

    if car_age <= 3:
        dep_zone = 1
    elif car_age <= 8:
        dep_zone = 2
    elif car_age <= 15:
        dep_zone = 3
    else:
        dep_zone = 4

    # STEP 1: KNN first - ground truth from real listings
    knn_price, best_dist, knn_prices = knn_estimate(
        brand, model_name, year, fuel, body, cond,
        trim, mileage, engine_cc, seats, doors, dep_zone
    )

    # STEP 2: routing - KNN price decides segment
    mz_key = f"{model_name}_z{dep_zone}"
    bz_key = f"{brand}_z{dep_zone}"
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

    # STEP 3: XGBoost prediction
    xgb_price, confidence, mae, mape, rows = run_segment(
        brand, model_name, body, fuel, cond, trim,
        year, car_age, mileage, engine_cc, seats, doors, mpy, dep_zone, segment
    )

    # STEP 4: blend KNN + XGBoost
    w_knn = 0
    if knn_price is not None and best_dist is not None:
        if best_dist == 0:
            w_knn = 0.95
        elif best_dist < 5:
            w_knn = 0.85
        elif best_dist < 12:
            w_knn = 0.65
        elif best_dist < 20:
            w_knn = 0.45
        else:
            w_knn = 0.25
        final_price = (w_knn * knn_price) + ((1 - w_knn) * xgb_price)
        print(f"Blend: XGB={xgb_price:,.0f} KNN={knn_price:,.0f} w_knn={w_knn:.2f} -> {final_price:,.0f}")
    else:
        final_price = xgb_price
        print(f"XGBoost only: {final_price:,.0f}")

    predicted = int(max(1000.0, round(final_price / 500) * 500))

    # STEP 5: range
    pmin, pmax = price_range(predicted, mape)

    verdict = get_verdict(car.user_price, predicted) if (car.user_price and car.user_price > 0) else None

    qid = str(uuid.uuid4())[:8]
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO queries
            (id,brand,model,year,fuel,body_style,car_condition,trim_level,
             mileage_km,engine_cc,seats,doors,user_price,predicted_price,
             price_min,price_max,segment,mileage_assumed,knn_price,knn_dist)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (qid, brand, car.model, year, fuel, body, cond, trim,
              car.mileage_km, engine_cc, seats, doors, car.user_price,
              predicted, pmin, pmax, segment, mileage_assumed, knn_price, best_dist))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB warning: {e}")

    return {
        "predicted_price": predicted,
        "price_range": {"min": pmin, "max": pmax},
        "confidence": confidence,
        "verdict": verdict,
        "mileage_assumed": mileage_assumed,
        "mileage_used": int(round(mileage)),
        "segment": segment,
        "model_info": {
            "segment": segment,
            "training_rows": rows,
            "mae": int(round(mae)),
            "mape": round(mape, 1),
            "knn_used": knn_price is not None,
            "knn_weight": round(w_knn, 2),
        }
    }


@router.post("/submit")
def submit_price(data: SubmitInput):
    if data.user_price <= 0:
        raise HTTPException(400, "Price must be positive")
    if data.user_price > 2000000:
        raise HTTPException(400, "Price seems unrealistic")
    ratio = data.user_price / max(data.predicted_price, 1)
    if ratio > 5.0 or ratio < 0.2:
        raise HTTPException(400, "Price too far from estimate")

    sid = str(uuid.uuid4())[:8]
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO submissions
            (id,brand,model,year,fuel,body_style,car_condition,trim_level,
             mileage_km,engine_cc,user_price,predicted_price,segment)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (sid, data.brand, data.model, data.year, data.fuel, data.body_style,
              data.car_condition, data.trim_level, data.mileage_km, data.engine_cc,
              data.user_price, data.predicted_price, data.segment))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")

    return {"success": True, "message": "Thank you."}
