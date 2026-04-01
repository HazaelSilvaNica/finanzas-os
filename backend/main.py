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
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/api/v1/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# ─────────────────────────────────────────────
#  AI Advice (Gemini Proxy)
# ─────────────────────────────────────────────
@app.post("/api/v1/analysis/ai-advice", tags=["IA"])
async def ai_advice(payload: dict):
    from supabase_client import supabase
    from datetime import timedelta
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise HTTPException(status_code=503, detail="No Gemini API Key")
    
    # 1. Fetch last 30 days of context from Supabase
    ago_30 = (date.today() - timedelta(days=30)).isoformat()
    res = supabase.table('transactions').select("*").filter('fecha', 'gte', ago_30).execute()
    txs = res.data
    
    # 2. Aggregates for AI
    summary_str = "\n".join([f"- {t['fecha'][:10]}: {t['entidad']} | {t['tipo']} | {t['monto']} {t['descripcion']} ({t['categoria']})" for t in txs[:50]])
    
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    system_instr = f"Eres un CFO Virtual experto. Analiza estos movimientos de los últimos 30 días:\n{summary_str}\n\nPregunta del usuario: "
    user_prompt = payload.get("prompt", "Analiza mis finanzas y dame 3 consejos de ahorro.")
    
    try:
        response = model.generate_content(system_instr + user_prompt)
        return {"analysis": response.text}
    except Exception as e:
        logger.error(f"AI Advice Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Server index for static UI
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
