import os
import sys
import logging
import traceback

# Vercel Path Resolution: Ensure local imports (database, api_v1) work first
sys.path.insert(0, os.path.dirname(__file__))
import uuid
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Depends, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import httpx
import google.generativeai as genai

load_dotenv()

# Pre-configuration - Using Environment Variables exclusively for security
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logging.warning("⚠️ GOOGLE_API_KEY missing. Ian AI features will be limited.")
UPLOADS_DIR = "/tmp/uploads"

# ─────────────────────────────────────────────
#  Safe Infrastructure Imports (Lazy)
# ─────────────────────────────────────────────
from database import init_db
from supabase_client import supabase
from odoo_client import odoo

# ─────────────────────────────────────────────
#  Logging & App Init
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("finanzasOS")

app = FastAPI(
    title="FinanzasOS 3.7",
    description="Sistema contable consolidado para Resiliencia en Vercel.",
    version="3.7.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hsragent.com",
        "https://www.hsragent.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Security Helper (Auth)
# ─────────────────────────────────────────────
def get_user_id(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    try:
        if not supabase: raise HTTPException(status_code=503, detail="Supabase Offline")
        user_res = supabase.auth.get_user(token)
        if not user_res.user: raise HTTPException(status_code=401, detail="Invalid session")
        
        # Admin restriction (Hazael)
        if user_res.user.email != "hazaelsilvanica@gmail.com":
            raise HTTPException(status_code=403, detail="Usuario no autorizado")
        return user_res.user.id
    except Exception as e:
        logger.error(f"Auth error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "version": "3.7.0", "env": os.getenv("VERCEL_ENV", "local")}

# ─────────────────────────────────────────────
#  Imports conditionally if they don't crash
# ─────────────────────────────────────────────
try:
    from api_v1 import router as v1_router
    app.include_router(v1_router)
except Exception as e:
    logger.error(f"Could not load v1_router due to imports: {e}")
    traceback.print_exc()

# ─────────────────────────────────────────────
#  Startup & Static
# ─────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    if not os.getenv("VERCEL"):
        try:
            init_db()
        except Exception: 
            traceback.print_exc()
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR, exist_ok=True)

try:
    app.mount("/api/v1/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
except: pass

if not os.getenv("VERCEL"):
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)
