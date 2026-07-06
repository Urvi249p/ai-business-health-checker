import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT_RETENTION_SECONDS = 10 * 60


def get_report_availability(job: dict[str, Any] | None, now: float | None = None) -> dict[str, Any]:
    """Return whether a completed report is still downloadable and when it expires."""
    if not job or str(job.get("status", "")).lower() != "completed":
        return {"report_available": False, "report_expires_at": None}

    result_path = job.get("result_path")
    if not result_path:
        return {"report_available": False, "report_expires_at": None}

    if now is None:
        now = time.time()

    completed_at = job.get("updated_at") or job.get("created_at")
    expires_at = None
    if completed_at:
        try:
            completed_dt = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
            if completed_dt.tzinfo is None:
                completed_dt = completed_dt.replace(tzinfo=timezone.utc)
            expires_at = completed_dt.timestamp() + REPORT_RETENTION_SECONDS
        except ValueError:
            expires_at = None

    if expires_at is None:
        return {"report_available": False, "report_expires_at": None}

    path = Path(result_path)
    available = bool(path.exists()) and now < expires_at
    expires_at_iso = datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()

    return {
        "report_available": available,
        "report_expires_at": expires_at_iso,
    }
