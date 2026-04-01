import os
import logging
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from api_v1 import router as v1_router

# ─────────────────────────────────────────────
#  Logging & App Init
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("finanzasOS")

# Initialize DB
logger.info("Initializing database...")
init_db()

app = FastAPI(
    title="FinanzasOS 2.0",
    description="Sistema contable avanzado con IA y soporte multimedia.",
    version="2.0.0"
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

# Routes
app.include_router(v1_router)

# ─────────────────────────────────────────────
#  Static Files
# ─────────────────────────────────────────────
UPLOADS_DIR = "/tmp/uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/api/v1/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# ─────────────────────────────────────────────
# AI endpoints are now managed in api_v1.py

# Server index for static UI
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
