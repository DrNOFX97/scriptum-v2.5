from datetime import datetime, timedelta
from collections import deque
import asyncio
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter para controlar requests ao site"""
    
    def __init__(self):
        self.settings = get_settings()
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Espera se necessário para respeitar rate limit"""
        async with self._lock:
            now = datetime.utcnow()
            
            # Limpar requests antigos (fora da janela)
            while self.requests and self.requests[0] < now - timedelta(minutes=1):
                self.requests.popleft()
            
            # Se estamos no limite, calcular tempo de espera
            if len(self.requests) >= self.settings.max_requests_per_minute:
                oldest_request = self.requests[0]
                wait_until = oldest_request + timedelta(minutes=1)
                
                if now < wait_until:
                    wait_seconds = (wait_until - now).total_seconds()
                    logger.info(f"Rate limit atingido, aguardando {wait_seconds:.1f}s")
                    await asyncio.sleep(wait_seconds)
                    
                    # Limpar novamente após espera
                    while self.requests and self.requests[0] < datetime.utcnow() - timedelta(minutes=1):
                        self.requests.popleft()
            
            # Registar novo request
            self.requests.append(datetime.utcnow())
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do rate limiter"""
        now = datetime.utcnow()
        recent_requests = [r for r in self.requests if r > now - timedelta(minutes=1)]
        
        return {
            "requests_last_minute": len(recent_requests),
            "limit": self.settings.max_requests_per_minute,
            "available": max(0, self.settings.max_requests_per_minute - len(recent_requests))
        }
