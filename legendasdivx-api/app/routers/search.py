from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
import time
from app.database import get_db
from app.models.subtitle import SearchRequest, SearchResponse, Language
from app.services.cache import CacheService
from app.services.rate_limiter import RateLimiter
from app.adapters.legendasdivx import LegendasDivxAdapter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
cache_service = CacheService()
rate_limiter = RateLimiter()
adapter = LegendasDivxAdapter()

@router.get("/search", response_model=SearchResponse)
async def search_subtitles(
    query: str = Query(..., min_length=2, description="Termo de pesquisa"),
    language: Optional[Language] = Query(None, description="Filtrar por idioma"),
    year: Optional[int] = Query(None, ge=1900, le=2100, description="Ano do filme/série"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de resultados"),
    use_cache: bool = Query(True, description="Usar cache se disponível"),
    db: Session = Depends(get_db)
):
    """
    Pesquisa legendas no LegendasDivx
    
    - **query**: Título do filme/série ou termo de pesquisa
    - **language**: Filtrar por idioma (pt-pt, pt-br, en, es, fr)
    - **year**: Filtrar por ano
    - **limit**: Número máximo de resultados
    - **use_cache**: Se deve usar resultados em cache
    """
    
    start_time = time.time()
    
    # Preparar filtros
    filters = {
        "language": language,
        "year": year,
        "limit": limit
    }
    
    # Verificar cache
    cached_results = None
    if use_cache:
        cached_results = cache_service.get_cached_search(db, query, filters)
    
    if cached_results:
        return SearchResponse(
            results=cached_results[:limit],
            total=len(cached_results),
            cached=True,
            search_time=time.time() - start_time
        )
    
    # Rate limiting
    await rate_limiter.wait_if_needed()
    
    try:
        # Pesquisar no site
        results = await adapter.search(query, language)
        
        # Filtrar por ano se especificado
        if year:
            results = [r for r in results if r.year == year or r.year is None]
        
        # Guardar em cache
        if results:
            cache_service.save_search_results(db, query, filters, results)
        
        return SearchResponse(
            results=results[:limit],
            total=len(results),
            cached=False,
            search_time=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"Erro na pesquisa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/stats")
async def search_stats():
    """Estatísticas do rate limiter"""
    return rate_limiter.get_stats()
