import numpy as np

from app.inference.loader import model_budget, model_mid, NUM_MEDIANS, BUDGET, MID
from app.inference.pricing import encode_label, get_confidence


def build_fv(brand, model_name, fuel, body, cond, trim,
             year, car_age, mileage, engine_cc, seats, doors,
             mpy, dep_zone, seg_fi):
    gm = seg_fi['global_mean']
    mc = seg_fi.get('model_counts', {})

    model_zone = f"{model_name}_z{int(dep_zone)}"
    brand_zone = f"{brand}_z{int(dep_zone)}"

    # Hierarchy: model_zone > brand_zone > global_mean
    mz_enc = float(seg_fi['target_means']['model_zone'].get(
        model_zone, seg_fi['target_means']['brand_zone'].get(brand_zone, gm)))
    bz_enc = float(seg_fi['target_means']['brand_zone'].get(brand_zone, gm))
    br_enc = float(seg_fi['target_means']['brand'].get(brand, gm))

    model_freq = float(mc.get(str(model_name or '').lower().strip(), 1.0))

    def num(v, col):
        if v is None:
            return NUM_MEDIANS.get(col, 0.0)
        try:
            f = float(v)
            return NUM_MEDIANS.get(col, 0.0) if np.isnan(f) else f
        except Exception:
            return NUM_MEDIANS.get(col, 0.0)

    return np.array([[
        mz_enc, bz_enc, br_enc,
        encode_label('fuel', fuel),
        encode_label('body_style', body),
        encode_label('car_condition', cond),
        encode_label('trim_level', trim),
        float(year), float(car_age), float(mileage),
        num(engine_cc, 'engine_cc_num'),
        num(seats, 'seats_num'),
        num(doors, 'doors_num'),
        float(mpy), float(dep_zone), model_freq,
    ]])


def run_segment(brand, model_name, body, fuel, cond, trim,
                year, car_age, mileage, engine_cc, seats, doors,
                mpy, dep_zone, seg_name):
    seg_fi = BUDGET if seg_name == 'budget' else MID
    seg_model = model_budget if seg_name == 'budget' else model_mid
    fv = build_fv(brand, model_name, fuel, body, cond, trim,
                  year, car_age, mileage, engine_cc, seats, doors,
                  mpy, dep_zone, seg_fi)
    raw = float(seg_model.predict(fv)[0])
    pred = max(1000.0, round(raw / 500) * 500)
    conf = get_confidence(model_name, brand, seg_fi)
    return pred, conf, seg_fi['mae'], seg_fi['mape'], seg_fi['training_rows']
