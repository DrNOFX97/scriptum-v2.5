from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.config import get_settings

Base = declarative_base()
settings = get_settings()

class CachedSearch(Base):
    __tablename__ = "cached_searches"
    
    id = Column(Integer, primary_key=True)
    query_hash = Column(String, unique=True, index=True)
    query_params = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

class DownloadHistory(Base):
    __tablename__ = "download_history"
    
    id = Column(Integer, primary_key=True)
    subtitle_id = Column(String, index=True)
    title = Column(String)
    release = Column(String)
    language = Column(String)
    file_path = Column(String)
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)

class RequestLog(Base):
    __tablename__ = "request_log"
    
    id = Column(Integer, primary_key=True)
    endpoint = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Integer)  # milliseconds
    success = Column(Boolean)

# Create engine and session
engine = create_engine(f"sqlite:///{settings.database_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
