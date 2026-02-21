from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List

class Language(str, Enum):
    PT_PT = "pt-pt"
    PT_BR = "pt-br"
    EN = "en"
    ES = "es"
    FR = "fr"

class SubtitleType(str, Enum):
    SRT = "srt"
    ASS = "ass"
    SUB = "sub"
    VTT = "vtt"

class SubtitleSearchResult(BaseModel):
    """Modelo para resultado de pesquisa"""
    id: str
    title: str
    release: str  # e.g., "BluRay.1080p.x264-GRUPO"
    language: Language
    uploader: str
    downloads: int
    rating: Optional[float] = None
    hearing_impaired: bool = False
    fps: Optional[float] = None
    upload_date: Optional[datetime] = None
    
    # Metadata adicional
    imdb_id: Optional[str] = None
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    
    # Para cache
    source: str = "legendasdivx"
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

class SubtitleDetails(SubtitleSearchResult):
    """Modelo estendido com detalhes completos"""
    description: Optional[str] = None
    file_size: Optional[int] = None  # bytes
    file_name: Optional[str] = None
    download_url: Optional[str] = None
    preview: Optional[str] = None  # Primeiras linhas do subtitle

class SearchRequest(BaseModel):
    """Request para pesquisa"""
    query: str
    language: Optional[Language] = None
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    limit: int = Field(default=20, le=100)

class SearchResponse(BaseModel):
    """Response da pesquisa"""
    results: List[SubtitleSearchResult]
    total: int
    cached: bool = False
    search_time: float  # segundos
