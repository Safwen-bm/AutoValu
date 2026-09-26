from app.inference.loader import le_encoders


def clean_brand(brand: str) -> str:
    return {'mercedes-benz': 'mercedes', 'citroën': 'citroen'}.get(
        brand.lower().strip(), brand.lower().strip()
    )


def encode_label(col: str, val) -> float:
    le = le_encoders[col]
    v = str(val).lower().strip()
    if v not in le.classes_:
        v = 'unknown'
    return float(le.transform([v])[0])


def get_confidence(model_name, brand, seg_fi):
    mc = seg_fi.get('model_counts', {})
    count = mc.get(str(model_name or '').lower().strip(), 0)
    if count >= 10:
        return {"level": "high", "message": "High confidence based on real listings of this model", "color": "green"}
    elif count >= 3:
        return {"level": "medium", "message": "Medium confidence estimated from similar models of this brand", "color": "yellow"}
    else:
        return {"level": "low", "message": "Low confidence limited data for this model", "color": "orange"}


def get_verdict(user_price, predicted):
    diff = (user_price - predicted) / predicted * 100
    if diff <= -15:
        return {"verdict": "excellent_deal", "label": "Excellent deal", "color": "green",
                "diff_pct": round(diff, 1), "message": f"This price is {abs(diff):.0f}% below market. Great deal.",
                "counter_offer": None}
    elif diff <= 10:
        return {"verdict": "fair_price", "label": "Fair price", "color": "yellow",
                "diff_pct": round(diff, 1), "message": "This price is within the normal market range.",
                "counter_offer": None}
    elif diff <= 25:
        return {"verdict": "expensive", "label": "A bit expensive", "color": "orange",
                "diff_pct": round(diff, 1), "message": f"This price is {diff:.0f}% above market. Try to negotiate.",
                "counter_offer": int(round(predicted * 0.94 / 500) * 500)}
    else:
        return {"verdict": "overpriced", "label": "Overpriced", "color": "red",
                "diff_pct": round(diff, 1), "message": f"This price is {diff:.0f}% above market. Walk away or negotiate hard.",
                "counter_offer": int(round(predicted * 0.90 / 500) * 500)}


def price_range(predicted, mape):
    """
    Tiered range cap - tighter for expensive cars, wider for cheap ones.
    """
    if predicted >= 100000:
        pct = 0.08
    elif predicted >= 50000:
        pct = 0.10
    else:
        pct = 0.12

    unc = predicted * pct
    pmin = int(max(1000, round((predicted - unc) / 500) * 500))
    pmax = int(round((predicted + unc) / 500) * 500)
    return pmin, pmax
