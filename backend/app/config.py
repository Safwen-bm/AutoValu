import os
from dotenv import load_dotenv

load_dotenv()

# backend/ root (one level above this app/ package)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where training writes and inference reads model artifacts.
ARTIFACTS_DIR = os.path.join(BASE_DIR, 'artifacts')

# Where the cleaned training data lives.
DATA_DIR = os.path.join(BASE_DIR, 'data')

DB_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://autovalu:autovalu123@localhost:5432/autovalu'
)

# Was hardcoded in api.py before — now pulled from env, with a local-dev fallback.
# Make sure ADMIN_SECRET is set for real once you deploy.
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'autovalu_admin_2026')
ADMIN_USER = os.environ.get('ADMIN_USERNAME')
ADMIN_PASS = os.environ.get('ADMIN_PASSWORD')
