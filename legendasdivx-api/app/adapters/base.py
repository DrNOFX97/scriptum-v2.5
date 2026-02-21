from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.subtitle import SubtitleSearchResult, Language

class SubtitleProvider(ABC):
    """Interface base para providers de legendas"""
    
    @abstractmethod
    async def search(self, query: str, language: Optional[Language] = None) -> List[SubtitleSearchResult]:
        """Pesquisa legendas"""
        pass
    
    @abstractmethod
    async def download(self, subtitle_id: str) -> bytes:
        """Download de legenda por ID"""
        pass
    
    @abstractmethod
    async def get_details(self, subtitle_id: str) -> Dict[str, Any]:
        """Obtém detalhes de uma legenda"""
        pass
