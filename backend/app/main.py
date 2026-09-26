from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import predict, admin, stats

app = FastAPI(title="AutoValu", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    print("\nAutoValu backend ready - model_zone encoding + KNN range")
    print("Docs: http://localhost:8000/docs\n")
