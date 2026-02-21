from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import aiofiles
from app.database import get_db, DownloadHistory
from app.services.rate_limiter import RateLimiter
from app.adapters.legendasdivx import LegendasDivxAdapter
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
rate_limiter = RateLimiter()
adapter = LegendasDivxAdapter()
settings = get_settings()

@router.get("/download/{subtitle_id}")
async def download_subtitle(
    subtitle_id: str,
    db: Session = Depends(get_db)
):
    """
    Download de uma legenda específica
    
    - **subtitle_id**: ID da legenda (obtido na pesquisa)
    """
    
    # Verificar se já temos o ficheiro
    existing = db.query(DownloadHistory).filter(
        DownloadHistory.subtitle_id == subtitle_id
    ).first()
    
    if existing and Path(existing.file_path).exists():
        logger.info(f"Servindo ficheiro existente: {subtitle_id}")
        return FileResponse(existing.file_path)
    
    # Rate limiting
    await rate_limiter.wait_if_needed()
    
    try:
        # Download do site
        content = await adapter.download(subtitle_id)
        
        # Guardar ficheiro
        file_path = Path(settings.download_dir) / f"{subtitle_id}.zip"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Registar na BD
        download_record = DownloadHistory(
            subtitle_id=subtitle_id,
            file_path=str(file_path),
            file_size=len(content)
        )
        db.add(download_record)
        db.commit()
        
        logger.info(f"Download concluído: {subtitle_id}")
        
        return FileResponse(
            file_path,
            media_type="application/zip",
            filename=f"subtitle_{subtitle_id}.zip"
        )
        
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{subtitle_id}/info")
async def subtitle_info(subtitle_id: str):
    """Informações detalhadas sobre uma legenda"""
    try:
        details = await adapter.get_details(subtitle_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
