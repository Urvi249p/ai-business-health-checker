"""
health_router.py — a simple /health endpoint.

Why have this?
  During development you want a dead-simple way to verify:
    - The server booted without errors
    - The database is reachable
    - Settings loaded correctly

  Hit it with:  GET http://127.0.0.1:8000/api/v1/health
  Or in browser: http://127.0.0.1:8000/api/v1/health

  A 200 response means Phase 1 is working perfectly.
"""

from fastapi import APIRouter
from src.config.settings import settings
from src.config.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Returns server status, config snapshot, and a DB connectivity check.

    This endpoint:
      1. Confirms the server is running
      2. Shows which model and DB file are configured
      3. Actually opens a DB connection and runs a query — so if SQLite
         is broken, this will return db_status: "error" with a message
    """

    # Try to open the DB and run a trivial query
    # If this fails, something is wrong with the database setup
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        await db.close()
        db_status = "ok"
        db_error = None
    except Exception as e:
        db_status = "error"
        db_error = str(e)

    return {
        "status": "ok",
        "message": "Business Audit API is running",
        "config": {
            "model": settings.MODEL_NAME,
            "database": settings.DATABASE_URL,
            "temp_dir": settings.TEMP_DIR,
            "log_level": settings.LOG_LEVEL,
        },
        "database": {
            "status": db_status,
            "error": db_error,
        },
    }