from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import get_settings
from datetime import datetime

router = APIRouter()
settings = get_settings()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    
    # Verificar DB
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "api": "healthy"
        },
        "version": "0.1.0"
    }

@router.get("/health/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """Health check detalhado com estatísticas"""
    
    # Contar registos
    from app.database import CachedSearch, DownloadHistory, RequestLog
    
    cached_searches = db.query(CachedSearch).count()
    downloads = db.query(DownloadHistory).count()
    requests = db.query(RequestLog).count()
    
    return {
        "status": "healthy",
        "stats": {
            "cached_searches": cached_searches,
            "total_downloads": downloads,
            "total_requests": requests
        },
        "config": {
            "cache_ttl_hours": settings.cache_ttl_hours,
            "rate_limit": settings.max_requests_per_minute
        }
    }
