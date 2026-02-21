from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from rich.logging import RichHandler
from app.config import get_settings
from app.database import init_db
from app.routers import search, download, health

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando Subtitle API...")
    init_db()
    logger.info("✅ Base de dados inicializada")
    
    yield
    
    # Shutdown
    logger.info("👋 A desligar Subtitle API...")

# Criar app
app = FastAPI(
    title="Subtitle API",
    description="API interna para pesquisa e download de legendas",
    version="0.1.0",
    lifespan=lifespan
)

# CORS (para desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(health.router, tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(download.router, prefix="/api/v1", tags=["download"])

@app.get("/")
async def root():
    return {
        "name": "Subtitle API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
