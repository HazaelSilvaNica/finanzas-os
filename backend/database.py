import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Path to local SQLite DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'finanzas_os.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
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
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
