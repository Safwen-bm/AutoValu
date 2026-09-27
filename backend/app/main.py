import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import predict, admin, stats

IS_PROD = os.environ.get("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title="AutoValu",
    version="5.0.0",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(predict.router)
app.include_router(admin.router)
app.include_router(stats.router)

try:
    init_db()
except Exception as e:
    print(f"DB WARNING: {e}")


@app.on_event("startup")
def startup_log():
    print("\nAutoValu backend ready - model_zone encoding + KNN range\n")