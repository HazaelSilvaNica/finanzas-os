import os
import logging
import uuid
import io
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends, Form, Header
from odoo_client import odoo
import base64
from openai import OpenAI
from supabase_client import supabase
import google.generativeai as genai
from PIL import Image
import pillow_heif
import fitz  # PyMuPDF

def _check_supabase():
    """Ensure Supabase connection is persistent."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase connection lost")
    return supabase

def get_user_id(authorization: str = Header(None)):
    """Verifica el token JWT de Supabase y extrae el user_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    try:
        # Usamos el cliente de Supabase para verificar el token
        user_res = supabase.auth.get_user(token)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        # Restricción de correo admin
        admin_email = "hazaelsilvanica@gmail.com"
        if user_res.user.email != admin_email:
            raise HTTPException(status_code=403, detail="Acceso denegado: Usuario no autorizado")
            
        return user_res.user.id
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger("finanzasOS.v1")

# Configuración Gemini
GOOGLE_API_KEY = "AIzaSyC4BYndjbqdX9FknsGqfTiK167x6s8quCI"
genai.configure(api_key=GOOGLE_API_KEY)

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ─────────────────────────────────────────────
#  Generative AI - Gemini 3 Flash
# ─────────────────────────────────────────────
async def process_document_with_gemini(file_content: bytes, mime_type: str):
    """Procesa el documento con Gemini y extrae JSON estricto."""
    model = genai.GenerativeModel('gemini-1.5-flash') # Usamos 1.5-flash como motor base para Gemini 3
    
    prompt = """
    Eres un experto contable y financiero. Analiza el documento adjunto (ticket, factura o estado de cuenta).
    Extrae la información y devuélvela UNICAMENTE en formato JSON puro, sin markdown ni explicaciones.
    
    Campos obligatorios:
    - monto: (Number) El total pagado.
    - fecha: (ISO format YYYY-MM-DD)
    - concepto: (Nombre del establecimiento o comercio)
    - categoria: (Sugerencia basada en: nomina, marketing, logistica, servicios, insumos, renta, software_ia, comisiones, impuestos, otros)
    - entidad: ('BUSINESS' si es ElectriGanadero/Logística/Negocio, 'PERSONAL' si es gasto personal/hogar)
    
    Si es un estado de cuenta Banamex o similar, identifica específicamente comisiones bancarias o pagos de impuestos (IVA/ISR).
    Si no encuentras un campo, devuelve null.
    """
    
    try:
        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_content}
        ])
        
        text = response.text.replace('```json', '').replace('```', '').strip()
        import json
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini processing error: {str(e)}")
        return None

@router.post("/ocr/process")
async def process_doc(
    archivo: UploadFile = File(...),
    user_id: str = Depends(get_user_id)
):
    """Endpoint para procesar tickets/PDFs con Gemini."""
    try:
        content = await archivo.read()
        mime_type = archivo.content_type
        filename = f"{uuid.uuid4()}_{archivo.filename}"
        
        # 1. Soporte HEIC
        if mime_type == "image/heic" or archivo.filename.lower().endswith('.heic'):
            heif_file = pillow_heif.read_heif(content)
            image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
            with io.BytesIO() as output:
                image.save(output, format="JPEG")
                content = output.getvalue()
                mime_type = "image/jpeg"
                filename = filename.replace('.heic', '.jpg')

        # 2. Subir a Supabase Storage (Privado)
        # Bucket: docs, Path: /user_id/docs/
        storage_path = f"{user_id}/docs/{filename}"
        supabase.storage.from_("docs").upload(storage_path, content, {"content-type": mime_type})

        # 3. Limpieza de archivos antiguos (> 24h)
        # Esto se podría hacer con un cron, pero aquí lo hacemos on-demand simplificado
        try:
            files = supabase.storage.from_("docs").list(f"{user_id}/docs")
            now = datetime.now()
            for f in files:
                created_at = datetime.fromisoformat(f['created_at'].replace('Z', '+00:00'))
                if now - created_at.replace(tzinfo=None) > timedelta(hours=24):
                    supabase.storage.from_("docs").remove(f"{user_id}/docs/{f['name']}")
        except Exception as ex:
            logger.warning(f"Cleanup error: {str(ex)}")

        # 4. Procesar con Gemini
        result = await process_document_with_gemini(content, mime_type)
        if not result:
             raise HTTPException(status_code=500, detail="Gemini no pudo procesar el documento")

        return result

    except Exception as e:
        logger.error(f"Error en process-doc: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
def _clasificar_gasto_empresarial(nombre: str) -> str:
    nombre_lower = str(nombre).lower()
    if any(k in nombre_lower for k in ["envia", "guía", "guia", "paquete", "envío", "logistica", "logística"]): return "logistica"
    if any(k in nombre_lower for k in ["marketing", "ads", "facebook", "meta", "publicidad", "instagram"]): return "marketing"
    if any(k in nombre_lower for k in ["zulema", "carolina", "eunice", "rosado", "mario", "gastelum", "nómina", "nomina", "sueldo"]): return "nomina"
    if any(k in nombre_lower for k in ["comisión", "comision", "bono"]): return "comisiones"
    if any(k in nombre_lower for k in ["cerca", "insumo", "malla", "electrico", "pastoreo", "herramienta"]): return "insumos"
    if any(k in nombre_lower for k in ["renta", "arrendamiento", "local"]): return "renta"
    if any(k in nombre_lower for k in ["starlink", "luz", "agua", "internet", "servicios"]): return "servicios"
    if any(k in nombre_lower for k in ["odoo", "chatgpt", "openai", "anthropic", "software", "ia"]): return "software_ia"
    return "otros"

def _clasificar_gasto_personal(nombre: str, monto: float = 0) -> str:
    nombre_lower = str(nombre).lower()
    if any(k in nombre_lower for k in ["comida", "súper", "super", "despensa", "walmart", "soriana", "oxxo"]): return "comida_super"
    if any(k in nombre_lower for k in ["gasolina", "gasolinera", "pemex", "combustible"]): return "gasolina"
    if any(k in nombre_lower for k in ["farmacia", "medicina", "doctor", "salud"]): return "salud"
    if any(k in nombre_lower for k in ["bacalar", "tours", "tour", "diversion", "entretenimiento", "cine", "playa"]): return "entretenimiento"
    if any(k in nombre_lower for k in ["retiro", "atm", "cajero", "efectivo"]): return "retiros_atm"
    if any(k in nombre_lower for k in ["amazon", "compras", "tienda", "ropa"]): return "compras"
    if any(k in nombre_lower for k in ["casa", "renta", "luz", "agua", "internet", "hogar"]): return "servicios_hogar"
    return "otros"

# ─────────────────────────────────────────────
#  ENDPOINTS - BUSINESS (Eléctrica Ganadero)
# ─────────────────────────────────────────────

@router.get("/business/summary")
def get_business_summary(anio: Optional[int] = Query(None), mes: Optional[int] = Query(None), user_id: str = Depends(get_user_id)):
    hoy = date.today()
    anio_q = anio or hoy.year
    mes_q = mes or hoy.month
    clave_mes = f"{anio_q}-{mes_q:02d}"
    
    import calendar
    primer_dia = f"{anio_q}-{mes_q:02d}-01"
    ultimo_dia = f"{anio_q}-{mes_q:02d}-{calendar.monthrange(anio_q, mes_q)[1]}"
    
    try:
        # Odoo Integration (Incomes)
        ventas_raw = odoo.search_read(
            model="sale.order", 
            domain=[["state", "in", ["sale", "done"]], ["date_order", ">=", f"{primer_dia} 00:00:00"], ["date_order", "<=", f"{ultimo_dia} 23:59:59"]],
            fields=["amount_total"]
        )
        ventas_total = sum(v.get("amount_total", 0) for v in ventas_raw)
        
        compras_raw = odoo.search_read(
            model="purchase.order",
            domain=[["state", "in", ["purchase", "done"]], ["date_approve", ">=", f"{primer_dia} 00:00:00"], ["date_approve", "<=", f"{ultimo_dia} 23:59:59"]],
            fields=["amount_total"]
        )
        compras_total = sum(c.get("amount_total", 0) for c in compras_raw)
        
        # Supabase Transactions - OPEX
        res_opex = supabase.table('transactions').select("monto").filter('entidad', 'eq', 'BUSINESS').filter('tipo', 'eq', 'EXPENSE').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
        opex_total = sum(item['monto'] for item in res_opex.data)
        
        # Supabase Transactions - Manual Income
        res_income = supabase.table('transactions').select("monto").filter('entidad', 'eq', 'BUSINESS').filter('tipo', 'eq', 'INCOME').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
        income_manual = sum(item['monto'] for item in res_income.data)

        total_ventas_final = ventas_total + float(income_manual)
        ganancia_neta = (total_ventas_final - compras_total) - float(opex_total)
        margen = (ganancia_neta / total_ventas_final * 100) if total_ventas_final > 0 else 0

        return {
            "periodo": clave_mes,
            "ventas": round(total_ventas_final, 2),
            "compras": round(compras_total, 2),
            "opex": round(float(opex_total), 2),
            "ganancia_neta": round(ganancia_neta, 2),
            "margen_neto": round(margen, 2),
            "health_score": "GREEN" if margen > 12 else ("YELLOW" if margen >= 5 else "RED")
        }
    except Exception as e:
        logger.exception("Error en business summary")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/business/expenses")
def get_business_expenses(anio: Optional[int] = Query(None), mes: Optional[int] = Query(None), categoria: Optional[str] = Query(None), user_id: str = Depends(get_user_id)):
    hoy = date.today()
    anio_q = anio or hoy.year
    mes_q = mes or hoy.month
    primer_dia = f"{anio_q}-{mes_q:02d}-01"
    import calendar
    ultimo_dia = f"{anio_q}-{mes_q:02d}-{calendar.monthrange(anio_q, mes_q)[1]}"
    
    query = supabase.table('transactions').select("*").filter('entidad', 'eq', 'BUSINESS').filter('tipo', 'eq', 'EXPENSE').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id)
    if categoria: query = query.filter('categoria', 'eq', categoria)
    
    res = query.order('fecha', desc=True).execute()
    txs = res.data
    
    resultado = [{
        "id": t['id'], "fecha": t['fecha'], "concepto": t['concepto'], 
        "monto": t['monto'], "categoria": t['categoria'], "file_url": t.get('file_url')
    } for t in txs]
    
    return {"total": sum(t['monto'] for t in txs), "registros": resultado}

# ─────────────────────────────────────────────
#  ENDPOINTS - PERSONAL
# ─────────────────────────────────────────────

@router.get("/personal/summary")
def get_personal_summary(anio: Optional[int] = Query(None), mes: Optional[int] = Query(None), user_id: str = Depends(get_user_id)):
    hoy = date.today()
    anio_q = anio or hoy.year
    mes_q = mes or hoy.month
    primer_dia = f"{anio_q}-{mes_q:02d}-01"
    import calendar
    ultimo_dia = f"{anio_q}-{mes_q:02d}-{calendar.monthrange(anio_q, mes_q)[1]}"
    
    res_in = supabase.table('transactions').select("monto").filter('entidad', 'eq', 'PERSONAL').filter('tipo', 'eq', 'INCOME').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
    ingresos = sum(item['monto'] for item in res_in.data)
    
    res_ex = supabase.table('transactions').select("monto").filter('entidad', 'eq', 'PERSONAL').filter('tipo', 'eq', 'EXPENSE').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
    gastos = sum(item['monto'] for item in res_ex.data)
    
    saldo = float(ingresos) - float(gastos)
    ahorro = (saldo / float(ingresos) * 100) if float(ingresos) > 0 else 0
    
    return {
        "periodo": f"{anio_q}-{mes_q:02d}", "ingresos": round(float(ingresos), 2), "gastos": round(float(gastos), 2),
        "saldo": round(saldo, 2), "tasa_ahorro": round(ahorro, 2),
        "health_score": "GREEN" if ahorro > 20 else ("YELLOW" if ahorro > 5 else "RED")
    }

@router.get("/personal/expenses")
def get_personal_expenses(anio: Optional[int] = Query(None), mes: Optional[int] = Query(None), categoria: Optional[str] = Query(None), user_id: str = Depends(get_user_id)):
    hoy = date.today()
    anio_q = anio or hoy.year
    mes_q = mes or hoy.month
    primer_dia = f"{anio_q}-{mes_q:02d}-01"
    import calendar
    ultimo_dia = f"{anio_q}-{mes_q:02d}-{calendar.monthrange(anio_q, mes_q)[1]}"
    
    query = supabase.table('transactions').select("*").filter('entidad', 'eq', 'PERSONAL').filter('tipo', 'eq', 'EXPENSE').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id)
    if categoria: query = query.filter('categoria', 'eq', categoria)
    
    res = query.order('fecha', desc=True).execute()
    txs = res.data
    
    return {"total": sum(t['monto'] for t in txs), "registros": [{ "id": t['id'], "fecha": t['fecha'], "concepto": t['concepto'], "monto": t['monto'], "categoria": t['categoria'] } for t in txs]}

# ─────────────────────────────────────────────
#  ENDPOINTS - OCR & AI
# ─────────────────────────────────────────────

@router.post("/ocr/process")
async def process_ticket_ocr(archivo: UploadFile = File(...), user_id: str = Depends(get_user_id)):
    """
    Recibe una imagen de ticket físico, la envía a OpenAI GPT-4o Vision
    y retorna la extracción de Monto, Fecha y Concepto.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Mock para desarrollo si no hay API Key
        logger.warning("OPENAI_API_KEY no configurada. Retornando mock.")
        return {
            "status": "mock",
            "extracted": {
                "monto": 450.00,
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "concepto": "Ticket de Prueba (Configura OpenAI API Key)",
                "entidad": "BUSINESS"
            }
        }

    client = OpenAI(api_key=api_key)
    
    # Leer imagen y convertir a base64
    content = await archivo.read()
    base64_image = base64.b64encode(content).decode('utf-8')

    prompt = """
    Analiza esta imagen de un ticket o factura. 
    Extrae los siguientes campos en formato JSON puro (sin markdown):
    {
       "monto": float,
       "fecha": "YYYY-MM-DD",
       "concepto": "Nombre del comercio o descripción corta",
       "entidad": "BUSINESS" o "PERSONAL",
       "categoria": "Sugerencia del catálogo"
    }
    
    CATÁLOGO BUSINESS: [logistica, marketing, nomina, insumos]
    CATÁLOGO PERSONAL: [comida_super, gasolina, entretenimiento]
    
    Si no encuentras un campo, pon null.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=300,
        )
        
        analysis = response.choices[0].message.content
        # Limpiar posible markdown
        analysis = analysis.replace("```json", "").replace("```", "").strip()
        import json
        return {"status": "success", "extracted": json.loads(analysis)}
        
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transactions")
async def add_transaction(
    monto: float = Form(...),
    tipo: str = Form(...),
    entidad: str = Form(...),
    concepto: str = Form(...),
    fecha: str = Form(...),
    categoria: Optional[str] = Form(None),
    archivo: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_user_id)
):
    file_url = None
    if archivo:
        try:
            ext = archivo.filename.split('.')[-1]
            fname = f"{uuid.uuid4()}.{ext}"
            content = await archivo.read()
            supabase.storage.from_('comprobantes').upload(
                path=fname,
                file=content,
                file_options={"content-type": archivo.content_type}
            )
            file_url_res = supabase.storage.from_('comprobantes').get_public_url(fname)
            file_url = file_url_res # Supabase library returns string or dict depending on version
            if isinstance(file_url, dict): file_url = file_url.get('publicUrl')
        except Exception as e:
            logger.error(f"Storage Error: {e}")

    tx_data = {
        "monto": monto, 
        "tipo": tipo.upper(), 
        "categoria": categoria,
        "concepto": concepto, 
        "entidad": entidad.upper(), 
        "fecha": fecha[:10], 
        "file_url": file_url,
        "user_id": user_id
    }
    
    res = supabase.table('transactions').insert(tx_data).execute()
    new_id = res.data[0]['id'] if res.data else str(uuid.uuid4())
    
    return {"status": "success", "id": new_id}

@router.put("/transactions/{tx_id}")
def update_transaction(tx_id: str, data: Dict, user_id: str = Depends(get_user_id)):
    update_data = {}
    if "monto" in data: update_data["monto"] = float(data["monto"])
    if "concepto" in data: update_data["concepto"] = data["concepto"]
    if "categoria" in data: update_data["categoria"] = data["categoria"]
    if "tipo" in data: update_data["tipo"] = data["tipo"].upper()
    if "fecha" in data: update_data["fecha"] = data["fecha"][:10]
    
    supabase.table('transactions').update(update_data).filter('id', 'eq', tx_id).filter('user_id', 'eq', user_id).execute()
    return {"status": "success"}

    supabase.table('transactions').update(update_data).filter('id', 'eq', tx_id).execute()
    return {"status": "success"}

@router.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: str, user_id: str = Depends(get_user_id)):
    supabase.table('transactions').delete().filter('id', 'eq', tx_id).filter('user_id', 'eq', user_id).execute()
    return {"status": "success"}

@router.get("/history")
def get_financial_history(entidad: str = Query("BUSINESS"), user_id: str = Depends(get_user_id)):
    """Trend report for the last 6 months."""
    _check_supabase()
    from datetime import date, timedelta
    hoy = date.today()
    meses_data = []
    
    for i in range(5, -1, -1):
        target_date = hoy.replace(day=1)
        for _ in range(i):
            target_date = (target_date - timedelta(days=1)).replace(day=1)
            
        clave_mes = target_date.strftime("%Y-%m")
        primer_dia = f"{clave_mes}-01"
        import calendar
        ultimo_dia = f"{clave_mes}-{calendar.monthrange(target_date.year, target_date.month)[1]}"
        
        res_in = supabase.table('transactions').select("monto").filter('entidad', 'eq', entidad.upper()).filter('tipo', 'eq', 'INCOME').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
        income = sum(item['monto'] for item in res_in.data)
        
        res_ex = supabase.table('transactions').select("monto").filter('entidad', 'eq', entidad.upper()).filter('tipo', 'eq', 'EXPENSE').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
        expense = sum(item['monto'] for item in res_ex.data)

        # Critical OpEx (Nomina/Envia)
        res_crit = supabase.table('transactions').select("monto").filter('entidad', 'eq', 'BUSINESS').filter('tipo', 'eq', 'EXPENSE').filter('categoria', 'in', '("nomina","envia_com")').filter('fecha', 'gte', primer_dia).filter('fecha', 'lte', ultimo_dia).filter('user_id', 'eq', user_id).execute()
        critical_opex = sum(item['monto'] for item in res_crit.data)
        
        meses_data.append({
            "mes": target_date.strftime("%b %Y"),
            "raw_mes": clave_mes,
            "ingresos": round(float(income), 2),
            "egresos": round(float(expense), 2),
            "critical_opex": round(float(critical_opex), 2)
        })
    return {"entidad": entidad.upper(), "historial": meses_data}

@router.get("/bi/summary")
def get_bi_summary(anio: Optional[int] = Query(None), mes: Optional[int] = Query(None), user_id: str = Depends(get_user_id)):
    """
    Business Intelligence Report: Ventas, Compras, Marketing, Comisiones.
    Calcula variación % vs mes anterior.
    """
    _check_supabase()
    hoy = date.today()
    anio_q = anio or hoy.year
    mes_q = mes or hoy.month
    
    # Rango Mes Actual
    import calendar
    start_curr = f"{anio_q}-{mes_q:02d}-01"
    end_curr = f"{anio_q}-{mes_q:02d}-{calendar.monthrange(anio_q, mes_q)[1]}"
    
    # Rango Mes Anterior
    prev_date = date(anio_q, mes_q, 1) - timedelta(days=1)
    anio_p, mes_p = prev_date.year, prev_date.month
    start_prev = f"{anio_p}-{mes_p:02d}-01"
    end_prev = f"{anio_p}-{mes_p:02d}-{calendar.monthrange(anio_p, mes_p)[1]}"

    def fetch_bi_metrics(start, end, y_anio, m_mes):
        # 🔴 Ventas (Odoo + Manual INCOME)
        ventas_odoo = sum(v.get("amount_total", 0) for v in odoo.search_read("sale.order", [["state","in",["sale","done"]],["date_order",">=",f"{start} 00:00:00"],["date_order","<=",f"{end} 23:59:59"]], ["amount_total"]))
        res_m = supabase.table('transactions').select("monto").filter('tipo','eq','INCOME').filter('entidad','eq','BUSINESS').filter('fecha','gte',start).filter('fecha','lte',end).filter('user_id', 'eq', user_id).execute()
        v_manual = sum(item['monto'] for item in res_m.data)
        
        # 🔴 Compras (EXPENSE + Compras/Inventario)
        res_c = supabase.table('transactions').select("monto").filter('tipo','eq','EXPENSE').filter('entidad','eq','BUSINESS').filter('categoria','eq','compras').filter('fecha','gte',start).filter('fecha','lte',end).filter('user_id', 'eq', user_id).execute()
        compras = sum(item['monto'] for item in res_c.data)
        
        # 🔴 Marketing
        res_mar = supabase.table('transactions').select("monto").filter('tipo','eq','EXPENSE').filter('entidad','eq','BUSINESS').filter('categoria','eq','marketing').filter('fecha','gte',start).filter('fecha','lte',end).filter('user_id', 'eq', user_id).execute()
        marketing = sum(item['monto'] for item in res_mar.data)
        
        # 🔴 Comisiones
        res_com = supabase.table('transactions').select("monto").filter('tipo','eq','EXPENSE').filter('entidad','eq','BUSINESS').filter('categoria','eq','comisiones').filter('fecha','gte',start).filter('fecha','lte',end).filter('user_id', 'eq', user_id).execute()
        comisiones = sum(item['monto'] for item in res_com.data)
        
        return {"ventas": ventas_odoo + v_manual, "compras": compras, "marketing": marketing, "comisiones": comisiones}

    curr = fetch_bi_metrics(start_curr, end_curr, anio_q, mes_q)
    prev = fetch_bi_metrics(start_prev, end_prev, anio_p, mes_p)

    def calc_var(c, p):
        if p == 0: return 100 if c > 0 else 0
        return round(((c - p) / p) * 100, 1)

    return {
        "periodo": f"{anio_q}-{mes_q:02d}",
        "metrics": {
            "ventas": {"total": curr["ventas"], "var": calc_var(curr["ventas"], prev["ventas"])},
            "marketing": {"total": curr["marketing"], "var": calc_var(curr["marketing"], prev["marketing"])},
            "comisiones": {"total": curr["comisiones"], "var": calc_var(curr["comisiones"], prev["comisiones"])}
        }
    }

@router.get("/history/yearly")
def get_yearly_history(entidad: str = "BUSINESS", anio: int = 2026, user_id: str = Depends(get_user_id)):
    """Evolución mensual para comparativos tipo Bar Chart."""
    _check_supabase()
    history = []
    for m in range(1, 13):
        start = f"{anio}-{m:02d}-01"
        import calendar
        end = f"{anio}-{m:02d}-{calendar.monthrange(anio, m)[1]}"
        
        res = supabase.table('transactions').select("monto").filter('entidad','eq',entidad.upper()).filter('tipo','eq','INCOME').filter('fecha','gte',start).filter('fecha','lte',end).filter('user_id', 'eq', user_id).execute()
        income = sum(i['monto'] for i in res.data)
        
        history.append({"mes_num": m, "mes": calendar.month_name[m][:3], "ingresos": income})
    return {"anio": anio, "data": history}

# ─────────────────────────────────────────────
#  ENDPOINTS - DEBTS & PASIVOS (v3.0)
# ─────────────────────────────────────────────

@router.get("/debts")
def get_debts(entidad: str = "BUSINESS", user_id: str = Depends(get_user_id)):
    _check_supabase()
    res = supabase.table('debts').select("*").filter('entity_type', 'eq', entidad.upper()).filter('is_active', 'eq', 'true').filter('user_id', 'eq', user_id).execute()
    return {"status": "success", "data": res.data}

@router.post("/debts")
def add_debt(data: Dict, user_id: str = Depends(get_user_id)):
    _check_supabase()
    data["user_id"] = user_id
    res = supabase.table('debts').insert(data).execute()
    return {"status": "success", "id": res.data[0]['id'] if res.data else None}

@router.delete("/debts/{debt_id}")
def delete_debt(debt_id: str, user_id: str = Depends(get_user_id)):
    _check_supabase()
    supabase.table('debts').update({"is_active": False}).filter('id', 'eq', debt_id).filter('user_id', 'eq', user_id).execute()
    return {"status": "success"}

# ─────────────────────────────────────────────
#  ENDPOINTS - ANALYTICS (v3.0)
# ─────────────────────────────────────────────

@router.get("/analysis/forecast")
def get_cashflow_forecast(entidad: str = "BUSINESS", user_id: str = Depends(get_user_id)):
    """
    Calcula el 'Runway' (Días de liquidez) basándose en el saldo actual
    vs. el promedio de gasto diario de los últimos 60 días.
    """
    _check_supabase()
    from datetime import timedelta
    hoy = date.today()
    fecha_limite = (hoy - timedelta(days=60)).isoformat()
    
    # 1. Calcular Burn Rate (Gasto promedio diario)
    res_ex = supabase.table('transactions').select("monto").filter('entidad', 'eq', entidad.upper()).filter('tipo', 'eq', 'EXPENSE').filter('fecha', 'gte', fecha_limite).filter('user_id', 'eq', user_id).execute()
    total_gasto = sum(item['monto'] for item in res_ex.data)
    daily_burn = total_gasto / 60 if total_gasto > 0 else 1 # Evitar div/0
    
    # 2. Calcular Liquidez Actual (Ingresos - Egresos histórico)
    res_all_in = supabase.table('transactions').select("monto").filter('entidad', 'eq', entidad.upper()).filter('tipo', 'eq', 'INCOME').filter('user_id', 'eq', user_id).execute()
    res_all_ex = supabase.table('transactions').select("monto").filter('entidad', 'eq', entidad.upper()).filter('tipo', 'eq', 'EXPENSE').filter('user_id', 'eq', user_id).execute()
    
    liquidez = sum(i['monto'] for i in res_all_in.data) - sum(e['monto'] for e in res_all_ex.data)
    
    runway_days = round(liquidez / daily_burn) if liquidez > 0 else 0
    
    return {
        "liquidez_actual": round(liquidez, 2),
        "daily_burn": round(daily_burn, 2),
        "runway_days": runway_days,
        "status": "HEALTHY" if runway_days > 15 else "CRITICAL"
    }

@router.get("/analysis/reconcile")
def get_reconciliation_report(user_id: str = Depends(get_user_id)):
    """
    Compara registros manuales vs. detecciones de OCR para resaltar
    posibles discrepancias o gastos olvidados.
    """
    _check_supabase()
    # Esta es una lógica simplificada para v3.0: 
    # Buscamos transacciones con evidence_url (OCR) y vemos si hay registros manuales
    # con montos idénticos en fechas similares.
    res = supabase.table('transactions').select("*").filter('user_id', 'eq', user_id).order('fecha', desc=True).limit(100).execute()
    all_txs = res.data
    
    # Separar en OCR (tienen file_url) y Manuales (no tienen)
    ocr_txs = [t for t in all_txs if t.get('file_url')]
    manual_txs = [t for t in all_txs if not t.get('file_url')]
    
    discrepancias = []
    for ocr in ocr_txs:
        # Buscar "match" por monto exacto
        match = any(abs(m['monto'] - ocr['monto']) < 0.01 for m in manual_txs)
        if not match:
            discrepancias.append({
                "monto": ocr['monto'],
                "fecha": ocr['fecha'],
                "concepto": ocr['concepto'],
                "reason": "Gasto detectado por OCR pero no registrado manualmente"
            })
            
    return {"status": "success", "discrepancies_found": len(discrepancias), "items": discrepancias}

@router.post("/ai/advice")
async def get_ai_advice(payload: Dict, user_id: str = Depends(get_user_id)):
    """
    Ian - El Asistente Financiero Senior. Proporciona consejos y responde dudas 
    basados en el contexto financiero actual del usuario.
    """
    context = payload.get("context", "business")
    data = payload.get("data", {})
    user_query = payload.get("prompt", "Dame un reporte estratégico de mi situación actual.")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    system_instruction = f"""
    Eres Ian, el CFO Virtual y Asesor Financiero Senior de Hazael Silva en su plataforma 'HSR Control'.
    
    CONTEXTO ACTUAL ({context.upper()}):
    {data}
    
    TU MISIÓN:
    1. Actúa como un experto financiero pragmático y proactivo. 
    2. Usa los números reales proporcionados para dar respuestas específicas. No seas genérico.
    3. Si detectas riesgos (ej. runway bajo, ROI negativo), menciónalos con soluciones claras.
    4. Responde en español con un tono profesional pero cercano, digno de un socio de confianza.
    5. Formatea tu respuesta con HTML ligero:
       - Usa <p> para párrafos.
       - Usa <strong> para resaltar cifras o conceptos clave.
       - Usa <ul class='list-disc pl-5 my-2'> <li> para listas de acciones.
    
    PREGUNTA DEL USUARIO:
    "{user_query}"
    """
    
    try:
        # Generamos contenido con el contexto y la duda específica
        response = model.generate_content(system_instruction)
        
        # Limpieza básica de markdown si Gemini ignora la instrucción de HTML
        advice_html = response.text.replace("```html", "").replace("```", "").strip()
        
        return {"advice": advice_html}
    except Exception as e:
        logger.error(f"Ian AI Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Ian está procesando datos complejos en este momento. Intenta de nuevo.")
