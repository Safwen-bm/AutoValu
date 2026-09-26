from fastapi import APIRouter

from app.database import get_db
from app.inference.loader import BUDGET, MID

router = APIRouter()


@router.get("/stats/public")
def public_stats():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM queries")
        total_checks = cur.fetchone()['c']
        cur.execute("""
            SELECT brand,COUNT(*) as count FROM queries
            WHERE brand IS NOT NULL AND brand!='' GROUP BY brand ORDER BY count DESC LIMIT 8
        """)
        top_brands = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT model,COUNT(*) as count FROM queries
            WHERE model IS NOT NULL AND model!='' GROUP BY model ORDER BY count DESC LIMIT 8
        """)
        top_models = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT ROUND(AVG(predicted_price)::numeric,0) as avg FROM queries
            WHERE predicted_price IS NOT NULL AND predicted_price>0
        """)
        avg_row = cur.fetchone()
        avg_price = float(avg_row['avg']) if avg_row['avg'] else 0
        cur.close()
        conn.close()
        return {"total_checks": total_checks, "top_brands": top_brands, "top_models": top_models, "avg_price": avg_price}
    except Exception:
        return {"total_checks": 0, "top_brands": [], "top_models": [], "avg_price": 0}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": "5.0.0",
        "segments": {
            "budget": {"mae": int(round(BUDGET['mae'])), "mape": round(BUDGET['mape'], 1), "rows": BUDGET['training_rows']},
            "mid": {"mae": int(round(MID['mae'])), "mape": round(MID['mape'], 1), "rows": MID['training_rows']},
        }
    }
