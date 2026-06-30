"""
database.py — async PostgreSQL via asyncpg.

Switched from aiosqlite (SQLite) to asyncpg (PostgreSQL).
All SQL syntax updated: ? placeholders → $1,$2,... (PostgreSQL style).
Everything else (function names, signatures) stays the same so the rest
of the app needs zero changes.

WHAT CHANGED vs the old SQLite version:
  - aiosqlite → asyncpg
  - Connection pool (asyncpg.Pool) instead of per-request connections
  - Placeholders: ? → $1, $2, $3 ...
  - Row access: same dict-style via asyncpg Records
  - init_db() uses PostgreSQL-compatible CREATE TABLE syntax
  - Added totp_secret + is_2fa_enabled columns to users table

TABLE: users
  id              TEXT PRIMARY KEY
  email           TEXT UNIQUE NOT NULL
  username        TEXT UNIQUE NOT NULL
  hashed_password TEXT NOT NULL
  created_at      TEXT NOT NULL
  totp_secret     TEXT          ← NEW (null until 2FA enabled)
  is_2fa_enabled  BOOLEAN       ← NEW (false by default)

TABLE: audit_jobs
  (unchanged)
"""

import asyncpg
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qs, urlsplit, urlunsplit

from src.config.settings import settings


# ── Connection Pool ───────────────────────────────────────────────────────────
# A pool keeps multiple connections open and reuses them across requests.
# Much more efficient than opening/closing a connection per request.

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """
    Return the global connection pool, creating it if needed.
    Handles PostgreSQL URLs with optional asyncpg scheme and sslmode query params.
    """
    global _pool
    if _pool is None:
        url = settings.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        ssl_mode = query.get("sslmode", [None])[0]

        clean_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", parsed.fragment))
        ssl = None
        if ssl_mode and ssl_mode.lower() != "disable":
            ssl = "require"

        _pool = await asyncpg.create_pool(
            clean_url,
            ssl=ssl,
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool() -> None:
    """Close the pool gracefully on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db():
    """
    Yield a connection from the pool.
    Usage:
        async with (await get_pool()).acquire() as conn:
            ...
    But most code calls the helper functions below instead.
    """
    pool = await get_pool()
    return pool


# ── Table creation ────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Create tables if they don't already exist.
    Called once at startup from main.py.
    Uses PostgreSQL syntax (no aiosqlite-specific calls).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # audit_jobs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_jobs (
                id                   TEXT PRIMARY KEY,
                status               TEXT NOT NULL DEFAULT 'queued',
                business_description TEXT NOT NULL,
                result_path          TEXT,
                error                TEXT,
                user_id              TEXT,
                created_at           TEXT NOT NULL,
                updated_at           TEXT NOT NULL
            )
        """)

        # users table — includes 2FA columns from the start
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              TEXT PRIMARY KEY,
                email           TEXT UNIQUE NOT NULL,
                username        TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                totp_secret     TEXT,
                is_2fa_enabled  BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)

        # Safe migrations — add columns if they don't exist yet
        # (handles existing DBs that were created before these columns)
        for column_sql in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE audit_jobs ADD COLUMN IF NOT EXISTS user_id TEXT",
        ]:
            await conn.execute(column_sql)


# ── Helper ────────────────────────────────────────────────────────────────────

def _now() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> dict | None:
    """Convert asyncpg Record to plain dict."""
    return dict(row) if row else None


# ── User functions ────────────────────────────────────────────────────────────

async def create_user(user_id: str, email: str, username: str, hashed_password: str) -> None:
    """Insert a new user. totp_secret=NULL, is_2fa_enabled=FALSE by default."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (id, email, username, hashed_password, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            user_id, email, username, hashed_password, _now(),
        )


async def get_user_by_username(username: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        return _row_to_dict(row)


async def get_user_by_email(email: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return _row_to_dict(row)


async def get_user_by_id(user_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return _row_to_dict(row)


# ── 2FA user functions ────────────────────────────────────────────────────────

async def enable_user_2fa(user_id: str, totp_secret: str) -> None:
    """Save TOTP secret and mark 2FA as enabled for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET totp_secret = $1, is_2fa_enabled = TRUE
            WHERE id = $2
            """,
            totp_secret, user_id,
        )


async def disable_user_2fa(user_id: str) -> None:
    """Clear TOTP secret and disable 2FA for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET totp_secret = NULL, is_2fa_enabled = FALSE
            WHERE id = $1
            """,
            user_id,
        )


# ── Audit job functions ───────────────────────────────────────────────────────

async def create_job(job_id: str, business_description: str, user_id: str = None) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO audit_jobs (id, status, business_description, created_at, updated_at, user_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            job_id, "queued", business_description, _now(), _now(), user_id,
        )


async def get_jobs_by_user(user_id: str) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM audit_jobs WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
        return [dict(r) for r in rows]


async def get_job(job_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM audit_jobs WHERE id = $1", job_id)
        return _row_to_dict(row)


async def update_job_status(job_id: str, status: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE audit_jobs SET status = $1, updated_at = $2 WHERE id = $3",
            status, _now(), job_id,
        )


async def complete_job(job_id: str, result_path: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE audit_jobs
            SET status = 'completed', result_path = $1, updated_at = $2
            WHERE id = $3
            """,
            result_path, _now(), job_id,
        )


async def fail_job(job_id: str, error: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE audit_jobs
            SET status = 'failed', error = $1, updated_at = $2
            WHERE id = $3
            """,
            error, _now(), job_id,
        )