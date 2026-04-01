import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Lazy initialization to avoid read-only filesystem crash at import time
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, 'data', 'finanzas_os.db')
        # On Vercel, we can only write to /tmp if absolutely needed
        if os.getenv("VERCEL"):
            db_path = "/tmp/finanzas_os.db"
        
        # Ensure directory exists if not on Vercel
        if not os.getenv("VERCEL"):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        DATABASE_URL = f"sqlite:///{db_path}"
        from sqlalchemy import create_engine
        _engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    monto = Column(Float, nullable=False)
    tipo = Column(String(20), nullable=False) # 'INCOME' o 'EXPENSE'
    categoria = Column(String(50), index=True)
    descripcion = Column(Text)
    entidad = Column(String(20), nullable=False) # 'BUSINESS' o 'PERSONAL'
    fecha = Column(DateTime, default=datetime.utcnow)
    file_url = Column(String(255), nullable=True) # Link al comprobante / multimedia
    iva_monto = Column(Float, default=0.0) # IVA automático (16%) para negocio
    is_external = Column(Boolean, default=False) # Para marcar si viene de Odoo automáticamente
    created_at = Column(DateTime, default=datetime.utcnow)

class AIContext(Base):
    __tablename__ = "ai_context"
    
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), unique=True, index=True) # Ej: 'user_meta_mahahual'
    valor = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=get_engine())

def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
