from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # LegendasDivx credentials
    legendasdivx_user: str
    legendasdivx_pass: str
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    
    # Rate limiting
    max_requests_per_minute: int = 10
    request_delay_seconds: int = 3
    
    # Cache settings
    cache_ttl_hours: int = 24
    database_path: str = "./data/subtitles.db"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/api.log"
    
    # Paths
    download_dir: str = "./data/downloads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Criar diretórios necessários
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

@lru_cache()
def get_settings():
    return Settings()
