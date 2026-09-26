from fastapi import APIRouter, HTTPException

from app.config import ADMIN_SECRET, ADMIN_USER, ADMIN_PASS
from app.database import get_db
from app.models.schemas import LoginInput

router = APIRouter(prefix="/admin")


@router.post("/login")
def admin_login(data: LoginInput):
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        return {"success": True, "token": ADMIN_SECRET}
    raise HTTPException(401, "Invalid credentials")


@router.get("/submissions")
def get_submissions(secret: str = "", status: str = "all"):
    if secret != ADMIN_SECRET:
        raise HTTPException(403, "Forbidden")
    conn = get_db()
    cur = conn.cursor()
    if status == "all":
        cur.execute("SELECT * FROM submissions ORDER BY timestamp DESC")
    else:
        cur.execute("SELECT * FROM submissions WHERE status=%s ORDER BY timestamp DESC", (status,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/review")
def review_submission(submission_id: str, action: str, secret: str = "", note: str = ""):
    if secret != ADMIN_SECRET:
        raise HTTPException(403, "Forbidden")
    if action not in ['approve', 'reject']:
        raise HTTPException(400, "approve or reject only")
    status = 'approved' if action == 'approve' else 'rejected'
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE submissions SET status=%s,admin_note=%s WHERE id=%s", (status, note, submission_id))
    if cur.rowcount == 0:
        raise HTTPException(404, "Not found")
    conn.commit()
    cur.close()
    conn.close()
    return {"success": True, "action": action, "id": submission_id}


@router.get("/stats")
def get_stats(secret: str = ""):
    if secret != ADMIN_SECRET:
        raise HTTPException(403, "Forbidden")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM queries")
    tq = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions")
    ts = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='pending'")
    tp = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='approved'")
    ta = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM submissions WHERE status='rejected'")
    tr = cur.fetchone()['c']
    cur.execute("SELECT brand,COUNT(*) as count FROM queries GROUP BY brand ORDER BY count DESC LIMIT 10")
    brands = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "total_queries": tq,
        "submissions": {"total": ts, "pending": tp, "approved": ta, "rejected": tr},
        "top_brands": [dict(r) for r in brands]
    }


@router.get("/queries")
def get_queries(secret: str = "", limit: int = 100):
    if secret != ADMIN_SECRET:
        raise HTTPException(403, "Forbidden")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM queries ORDER BY timestamp DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]
