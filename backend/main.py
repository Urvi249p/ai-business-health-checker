"""
main.py — FastAPI entry point.

Changes from original:
  - Added close_pool() on shutdown (PostgreSQL connection pool cleanup)
  - Everything else unchanged
"""
import os
os.environ["LITELLM_DROP_PARAMS"] = "true"
import asyncio
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.database import init_db, close_pool
from src.routes.auth_router import router as auth_router
from src.utils.cleanup import start_cleanup_worker
from src.utils.logger import logger

from src.routes.health_router import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    logger.info("Starting Business Audit API...")

    settings.validate()
    logger.info(f"Config OK — model: {settings.MODEL_NAME}, port: {settings.PORT}")

    await init_db()
    logger.info(f"PostgreSQL ready — {settings.DATABASE_URL}")

    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Temp dir ready at {settings.TEMP_DIR}")

    asyncio.create_task(start_cleanup_worker())
    logger.info("Cleanup worker started")

    logger.info("Startup complete. Server is ready.")

    yield  # server handles requests here

    # ── SHUTDOWN ──
    await close_pool()          # ← close PostgreSQL pool gracefully
    logger.info("Shutting down Business Audit API.")


app = FastAPI(
    title="Business Audit API",
    description="AI-powered business audit and strategy report generator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])

from src.routes.audit_router import router as audit_router
app.include_router(audit_router, prefix="/api/v1", tags=["Audit"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=True,
    )