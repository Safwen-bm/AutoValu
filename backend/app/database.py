from psycopg2 import connect
from psycopg2.extras import RealDictCursor

from app.config import DB_URL


def get_db():
    return connect(DB_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()
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
    conn.commit()
    cur.close()
    conn.close()
    print("PostgreSQL ready.")
