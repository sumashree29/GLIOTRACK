"""
Admin routes — all endpoints require role=admin JWT.
Fix #7  — /health is now behind require_admin, not public.
Fix #10 — rate limiter applied.
"""
import time
from fastapi import APIRouter, Depends, Request
from app.core.auth import require_admin
from app.core.rate_limit import api_limiter, get_client_ip

router = APIRouter(prefix="/admin", tags=["admin"])
_start_time = time.time()


@router.get("/health")
def health(request: Request, admin=Depends(require_admin)):
    # FIX #7 — admin-only, not public
    api_limiter.check(get_client_ip(request))
    uptime_s = int(time.time() - _start_time)
    hours, rem = divmod(uptime_s, 3600)
    minutes, seconds = divmod(rem, 60)
    qdrant_status = {
        "reachable": False,
        "host": None,
        "expected_collection": None,
        "collection_found": False,
        "point_count": 0,
        "error": None
    }
    try:
        from app.core.config import settings
        from rag.knowledge_base import _build_qdrant_client
        qdrant_status["host"] = settings.qdrant_url
        qdrant_status["expected_collection"] = settings.qdrant_collection_name
        
        client = _build_qdrant_client()
        collections = client.get_collections().collections
        col_names = [c.name for c in collections]
        qdrant_status["reachable"] = True
        
        if settings.qdrant_collection_name in col_names:
            qdrant_status["collection_found"] = True
            info = client.get_collection(settings.qdrant_collection_name)
            qdrant_status["point_count"] = info.points_count
    except Exception as exc:
        qdrant_status["error"] = str(exc)

    return {
        "status":          "ok",
        "service":         "brain-tumour-assessment",
        "version":         "1.0.0",
        "uptime":          f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        "uptime_seconds":  uptime_s,
        "qdrant":          qdrant_status,
    }
