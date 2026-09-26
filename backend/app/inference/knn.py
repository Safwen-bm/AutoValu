import numpy as np

from app.inference.loader import df_knn_full


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
        fuel_clean = str(fuel or '').lower().strip()
        body_clean = str(body_style or '').lower().strip()
        cond_clean = str(car_condition or '').lower().strip()
        trim_clean = str(trim_level or 'standard').lower().strip()

        def model_dist(rm):
            rm = str(rm).lower().strip()
            if rm == model_clean:
                return 0
            if model_clean and (model_clean in rm or rm in model_clean):
                return 2
            return 12

        subset['d_model'] = subset['model'].apply(model_dist)
        subset['d_year'] = abs(subset['year'].fillna(year) - year)
        subset['d_mile'] = abs(subset['mileage_num'].fillna(mileage) - mileage) / 15000
        subset['d_zone'] = abs(subset['depreciation_zone'].fillna(dep_zone) - dep_zone) * 3

        subset['d_fuel'] = subset['fuel'].apply(lambda f: 0 if str(f).lower().strip() == fuel_clean else 3)
        subset['d_body'] = subset['body_style'].apply(lambda b: 0 if str(b).lower().strip() == body_clean else 1)
        subset['d_cond'] = subset['car_condition'].apply(lambda c: 0 if str(c).lower().strip() == cond_clean else 2)
        subset['d_trim'] = subset['trim_level'].apply(lambda t: 0 if str(t).lower().strip() == trim_clean else 1)

        if engine_cc and engine_cc > 0:
            subset['d_cc'] = abs(subset['engine_cc_num'].fillna(engine_cc) - engine_cc) / 300
        else:
            subset['d_cc'] = 0

        subset['d_seats'] = abs(subset['seats_num'].fillna(seats or 5) - (seats or 5))
        subset['d_doors'] = abs(subset['doors_num'].fillna(doors or 4) - (doors or 4))

        subset['total_dist'] = (
            subset['d_model'] * 12.0 +
            subset['d_year'] * 6.0 +
            subset['d_mile'] * 3.0 +
            subset['d_zone'] * 3.0 +
            subset['d_fuel'] * 2.5 +
            subset['d_cond'] * 2.0 +
            subset['d_cc'] * 2.0 +
            subset['d_body'] * 1.5 +
            subset['d_trim'] * 1.0 +
            subset['d_seats'] * 0.5 +
            subset['d_doors'] * 0.5
        )

        closest = subset.nsmallest(5, 'total_dist')
        best_dist = float(closest['total_dist'].iloc[0])
        weights = 1.0 / (closest['total_dist'] + 0.1)
        knn_price = float(np.average(closest['price'], weights=weights))
        knn_prices = closest['price'].tolist()

        print(f"\nKNN: {brand} {model_clean} {year} | {int(mileage)}km | {fuel_clean} | {cond_clean}")
        print(closest[['model', 'year', 'mileage_num', 'fuel', 'car_condition', 'price', 'total_dist']].to_string(index=False))
        print(f"KNN: {knn_price:,.0f} DT | best_dist: {best_dist:.1f}")

        return knn_price, best_dist, knn_prices

    except Exception as e:
        print(f"KNN error: {e}")
        return None, None, []
