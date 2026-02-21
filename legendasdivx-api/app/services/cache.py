import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.database import CachedSearch
from app.models.subtitle import SubtitleSearchResult
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.settings = get_settings()
        
    def _generate_cache_key(self, query: str, filters: Dict[str, Any]) -> str:
        """Gera chave única para cache"""
        cache_string = f"{query}:{json.dumps(filters, sort_keys=True)}"
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    def get_cached_search(self, db: Session, query: str, filters: Dict[str, Any]) -> Optional[List[SubtitleSearchResult]]:
        """Busca resultados em cache"""
        cache_key = self._generate_cache_key(query, filters)
        
        cached = db.query(CachedSearch).filter(
            CachedSearch.query_hash == cache_key
        ).first()
        
        if cached and not cached.is_expired():
            logger.info(f"Cache hit para query: {query}")
            results = json.loads(cached.results)
            return [SubtitleSearchResult(**r) for r in results]
        
        return None
    
    def save_search_results(self, db: Session, query: str, filters: Dict[str, Any], results: List[SubtitleSearchResult]):
        """Guarda resultados em cache"""
        cache_key = self._generate_cache_key(query, filters)
        
        # Verificar se já existe
        existing = db.query(CachedSearch).filter(
            CachedSearch.query_hash == cache_key
        ).first()
        
        results_json = json.dumps([r.model_dump() for r in results], default=str)
        expires_at = datetime.utcnow() + timedelta(hours=self.settings.cache_ttl_hours)
        
        if existing:
            existing.results = results_json
            existing.created_at = datetime.utcnow()
            existing.expires_at = expires_at
        else:
            cached_search = CachedSearch(
                query_hash=cache_key,
                query_params=filters,
                results=results_json,
                expires_at=expires_at
            )
            db.add(cached_search)
        
        db.commit()
        logger.info(f"Resultados guardados em cache para: {query}")
    
    def clear_expired(self, db: Session):
        """Limpa cache expirado"""
        deleted = db.query(CachedSearch).filter(
            CachedSearch.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        
        if deleted > 0:
            logger.info(f"Removidas {deleted} entradas expiradas do cache")
