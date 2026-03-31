# FinanzasOS v3.5 (LiquidGlass)

**Sistema Integral de Gestión Financiera Empresarial y Personal**

Plataforma moderna que integra datos de Odoo SaaS con gestión personal de finanzas, OCR, e inteligencia artificial en una interfaz glassmorphism premium.

---

## ✨ Características

### 🏢 Entorno Empresarial (Eléctrica Ganadero)
- Sincronización automática con Odoo (Ventas, Compras)
- Cálculo de margen neto en tiempo real
- **Health Score** basado en rentabilidad (Verde >12%, Amarillo 5-12%, Rojo <5%)
- Categorización de gastos operativos: Envíos, Nómina, Software/IA, Servicios, etc.

### 👤 Entorno Personal (Hazael Silva)
- Ingresos fijos: $45,000/mes
- Auto-categorización de gastos: ⛽ Gasolina, 🍔 Comida, 💸 Retiros ATM, 🏥 Salud, etc.
- Cálculo de tasa de ahorro
- Health Score personal basado en capacidad de ahorro

### 📄 Módulo OCR Avanzado
- Carga de PDFs de Estado de Cuenta (Banamex)
- Extracción automática: Fecha, Concepto, Monto, Saldo
- Import masivo de transacciones personales
- Auto-clasificación inteligente

### 🤖 AI Analyst (Gemini Integration)
- 3 recomendaciones estratégicas mensuales
- Análisis contextual del perfil financiero
- Sugerencias accionables para optimizar margen neto

### 🎨 UI LiquidGlass
- Diseño moderno con glassmorphism y blur
- Animaciones fluidas
- Responsive (Desktop + Tablet)
- Dark mode ready

---

## 📋 Datos de Referencia (Marzo 2026)

| Concepto | Monto |
|----------|-------|
| **Ventas Odoo** | $685,808.00 |
| **Compras Odoo** | $539,120.00 |
| **Ganancia Bruta** | $146,688.00 |
| **OpEx (Manual)** | $54,393.75 |
| **Ganancia Neta** | $92,294.25 |
| **Margen Neto** | 13.45% ✅ GREEN |
| **Saldo Banamex** | $260,578.92 |
| **Ingresos Personales** | $45,000.00 |
| **Gastos Personales** | $10,813.28 |

---

## 🚀 Instalación Rápida

### Requisitos
- Python 3.9+
- Acceso a Odoo SaaS (API Key)
- API Key de Google Gemini (opcional pero recomendado)

### Paso 1: Backend Setup

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar template de .env
cp .env.example .env

# IMPORTANTE: Editar .env con tus credenciales
# - ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY
# - GEMINI_API_KEY (para AI Analyst)
```

### Paso 2: Iniciar Backend

```bash
# Desde el directorio backend/
uvicorn main:app --reload --port 8000

# Salida esperada:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### Paso 3: Frontend

```bash
# Opción A: Servir con Python
cd frontend
python -m http.server 5173

# Opción B: Usar Live Server (VS Code)
# Right-click en index.html → Open with Live Server

# Opción C: Abrir directamente
# file:///path/to/frontend/index.html
```

### Verificar Instalación

```bash
# Health check del backend en otra terminal
curl http://localhost:8000/api/health

# Respuesta esperada:
{
  "servidor": "FinanzasOS Backend v1.0",
  "estado": "online",
  "odoo": {
    "estado": "conectado",
    "version": "19.0.1.0.0"
  }
}
```

---

## 🔌 Endpoints de API

### Health & Status

**GET** `/api/health`
```
Verifica conexión backend y Odoo
No requiere autenticación
```

---

### Entorno Empresarial

#### GET `/api/v1/business/summary`
**Resumen financiero mensual**

Parámetros:
- `anio` (int, opcional): 2026
- `mes` (int, opcional): 1-12

Respuesta:
```json
{
  "periodo": "2026-03",
  "ventas": 685808.00,
  "compras": 539120.00,
  "ganancia_bruta": 146688.00,
  "opex": 54393.75,
  "ganancia_neta": 92294.25,
  "margen_neto": 13.45,
  "health_score": "GREEN",
  "health_label": "Excelente",
  "num_ordenes_venta": 47,
  "num_ordenes_compra": 32
}
```

#### GET `/api/v1/business/expenses`
**Listado detallado de gastos empresariales**

Parámetros:
- `anio` (int)
- `mes` (int)
- `categoria` (str): `envia_com`, `nomina`, `renta`, `software`, `servicios`, `impuestos`

Respuesta:
```json
{
  "periodo": "2026-03",
  "total": 54393.75,
  "count": 14,
  "por_categoria": {
    "envia_com": { "total": 23000.00, "registros": [...] },
    "nomina": { "total": 14925.00, "registros": [...] },
    "software": { "total": 11767.99, "registros": [...] }
  },
  "registros": [...]
}
```

---

### Entorno Personal

#### GET `/api/v1/personal/summary`
**Resumen financiero personal**

Respuesta:
```json
{
  "periodo": "2026-03",
  "ingresos": 45000.00,
  "gastos": 10813.28,
  "saldo_disponible": 34186.72,
  "tasa_ahorro_pct": 75.97,
  "health_score": "GREEN",
  "health_label": "Muy bueno",
  "num_transacciones": 8
}
```

#### GET `/api/v1/personal/expenses`
**Gastos personales categorizados**

Respuesta:
```json
{
  "periodo": "2026-03",
  "total": 10813.28,
  "count": 8,
  "por_categoria": {
    "retiros_atm": { "total": 4038.28, "registros": [...] },
    "comida": { "total": 3190.00, "registros": [...] },
    "gasolina": { "total": 780.00, "registros": [...] },
    "entretenimiento": { "total": 199.00, "registros": [...] },
    "transporte": { "total": 580.00, "registros": [...] },
    "salud": { "total": 245.00, "registros": [...] }
  },
  "registros": [...]
}
```

---

### Registro Manual

#### POST `/api/v1/expenses/manual`
**Registra gasto manual (empresarial o personal)**

Body:
```json
{
  "fecha": "2026-04-05",
  "concepto": "Gasolina PEMEX",
  "monto": 850.00,
  "is_business": false,
  "categoria": "gasolina"
}
```

Respuesta:
```json
{
  "status": "success",
  "expense": { /* ...expense... */ },
  "message": "Gasto personal registrado"
}
```

---

### OCR & PDF Processing

#### POST `/api/v1/analysis/upload-pdf`
**Procesa Estado de Cuenta PDF (Banamex)**

Cuerpo: `multipart/form-data` con archivo PDF

Respuesta:
```json
{
  "filename": "estado_marzo.pdf",
  "status": "success",
  "extracted_count": 15,
  "transactions": [
    {
      "fecha": "2026-03-25",
      "concepto": "COMIDA SR CHOW",
      "monto": 420.00,
      "is_business": false,
      "categoria": "comida",
      "source": "banamex_pdf"
    }
  ],
  "import_url": "/api/v1/analysis/import-banamex"
}
```

#### POST `/api/v1/analysis/import-banamex`
**Importa transacciones extraídas del PDF**

Body:
```json
{
  "transactions": [
    {
      "fecha": "2026-03-25",
      "concepto": "COMIDA",
      "monto": 420.00,
      "is_business": false
    }
  ]
}
```

Respuesta:
```json
{
  "imported": 15,
  "total_attempted": 15,
  "errors": null,
  "message": "Importadas 15/15 transacciones"
}
```

---

### AI Analysis

#### POST `/api/v1/analysis/ai-advice`
**Genera recomendaciones con Gemini**

Body:
```json
{
  "prompt": "Miliza en mi margen neto bajo el contexto: Ventas $685k, Compras $539k, OpEx $54k. Dame 3 estrategias."
}
```

Respuesta:
```json
{
  "analysis": "1. **Reducir OpEx en 10%**: Renegociar contratos de software...\n2. **Mejorar margen de venta**: Incrementar precio unitario...\n3..."
}
```

---

## 🎯 Flujos de Uso

### Flujo 1: Morning Dashboard
1. Backend sincroniza Odoo (sales, purchase orders)
2. Frontend muestra KPIs en tiempo real
3. Health score: 13.45% (GREEN)
4. Usuario ve: Ventas $685k, OpEx $54k, Ganancia $92k

### Flujo 2: Registro de Gasto Personal
1. Usuario: "Comida Sr. Chow $520"
2. Backend auto-clasifica como "comida"
3. Personal expenses: +$520
4. Tasa ahorro se recalcula (↓)
5. Health score si es necesario ajusta

### Flujo 3: Upload de Banamex
1. Usuario sube `estado_marzo.pdf`
2. OCR extrae 15 transacciones
3. Auto-categoriza: Pizza Hut → Comida, ATM → Retiros
4. Usuario revisa en preview
5. Click "Importar" → 15 gastos se guardan
6. Personal summary se actualiza

### Flujo 4: AI Analysis
1. Button "Asistente IA"
2. Frontend envía: ventas, compras, opex, margen
3. Gemini genera análisis en 3s
4. Panel lateral muestra 3 recomendaciones
5. Usuario toma decisiones

---

## 📁 Estructura de Proyecto

```
Finanzas Personales y Electriganadero/
├── README.md                     ← Este archivo
├── backend/
│   ├── main.py                   ← Servidor FastAPI
│   ├── api_v1.py                 ← Endpoints v1 (business, personal, OCR, AI)
│   ├── odoo_client.py            ← Cliente JSON-RPC (solo lectura)
│   ├── requirements.txt           ← pip install
│   ├── .env.example              ← Template
│   ├── .env                       ← Secretos (NO a Git)
│   └── data/
│       └── expenses_manual.json   ← DB local de gastos manuales
└── frontend/
    └── index.html                ← Dashboard Todo-en-1
```

---

## 🔒 Seguridad

### Principios
- ✅ **Read-only en Odoo**: Bloqueamos write/create/unlink en Python
- ✅ **Secrets en .env**: ODOO_API_KEY y GEMINI_API_KEY nunca en código
- ✅ **CORS compartimentado**: Solo localhost (file://, http://localhost)
- ✅ **is_business flag**: Separa gastos empresariales de personales

### Checklist Pre-Producción
- [ ] `.env` con credenciales reales
- [ ] ODOO_API_KEY validada (token de Odoo)
- [ ] GEMINI_API_KEY activada (Google Cloud)
- [ ] Backend corriendo en puerto 8000
- [ ] Frontend accesible en localhost:5173
- [ ] Prueba `/api/health` → online

---

## 🌡️ Sistema de Health Score

### Empresarial (Margen Neto %)
```
GREEN  (✅): > 12%    → Excelente
YELLOW (⚠️ ): 5-12%   → Aceptable
RED    (❌): < 5%     → Crítico
```

### Personal (Tasa Ahorro %)
```
GREEN  (✅): > 20%    → Muy bueno
YELLOW (⚠️ ): 5-20%   → Normal
RED    (❌): < 5%     → Déficit
```

---

## 📝 Categorías de Gastos

### Empresarial
- `envia_com`: Envios.com (guías, paquetes)
- `nomina`: Sueldos, comisiones
- `renta`: Renta del local
- `software`: Suscripciones (Odoo, ChatGPT, OpenAI, Anthropic)
- `servicios`: Internet, Starlink, luz
- `impuestos`: SAT, ISR, IVA

### Personal
- `gasolina`: Gasolina, PEMEX
- `comida`: Restaurantes (Sr. Chow, Pizza, KFC)
- `retiros_atm`: Retiros de efectivo
- `salud`: Farmacia, médico
- `entretenimiento`: Netflix, cine, streaming
- `transporte`: Uber, taxi
- `compras`: Amazon, Walmart
- `gastos_varios`: Otros

---

## 🆘 Troubleshooting

### ❌ "Connection refused" (Backend)
**Problema**: Frontend no puede conectarse a `http://localhost:8000`
**Solución**:
```bash
# Verificar que backend está corriendo
curl http://localhost:8000/api/health

# Si no responde, reiniciar backend
uvicorn main:app --reload --port 8000
```

### ❌ "GEMINI_API_KEY not configured"
**Problema**: AI Analyst no funciona
**Solución**:
1. Ir a [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Crear API Key
3. Agregarse a `.env`: `GEMINI_API_KEY=sk_...`
4. Reiniciar backend

### ❌ "Odoo connection failed"
**Problema**: Backend no conecta con Odoo
**Solución**:
```bash
# Verificar credenciales en .env
cat .env | grep ODOO

# Generar nueva API Key en Odoo:
# Odoo → Avatar → Seguridad → Nuevo Token API
```

### ❌ "PDF parsing error"
**Problema**: Subir PDF no extrae transacciones
**Solución**:
- Verificar que es PDF válido
- Asegurar que es de Banamex (estructura esperada)
- Ver logs de backend para detalles

---

## 📊 Testing Rápido

```bash
# 1. Health check
curl http://localhost:8000/api/health

# 2. Business summary
curl "http://localhost:8000/api/v1/business/summary?mes=3&anio=2026"

# 3. Personal summary
curl "http://localhost:8000/api/v1/personal/summary?mes=3&anio=2026"

# 4. Register manual expense
curl -X POST http://localhost:8000/api/v1/expenses/manual \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2026-04-05",
    "concepto": "Test Expense",
    "monto": 100.00,
    "is_business": false
  }'
```

---

## 📅 Roadmap Futuro

- [ ] Reportes PDF exportables
- [ ] Predicciones con Machine Learning
- [ ] Mobile app nativa (React Native)
- [ ] Integración bancaria directa (Plaid)
- [ ] Two-factor authentication
- [ ] Dashboard multiusuario
- [ ] Notificaciones de anomalías

---

## 🙋 FAQ

**¿Puedo usar esto con otra instancia de Odoo?**
Sí. Cambiar `ODOO_URL` y `ODOO_DB` en `.env`

**¿Es seguro subir mis gastos personales aquí?**
Sí. Te controlas la base de datos (JSON local). Nada se sube a servidor.

**¿Qué pasa si pierdo internet?**
El frontend sigue funcionando con datos en caché. Backend requiere conexión a Odoo.

**¿Puedo exportar los datos?**
Sí. El archivo `expenses_manual.json` es tuyo. También puedes hacer backup de Odoo.

---

## 📞 Soporte

**Desenvolvedor**: Hazael Silva  
**RFC**: SIRH910326BN7  
**Email**: electriganadero.apps@gmail.com  

---

**Última actualización**: 30 Marzo 2026  
**Versión**: 3.5 (LiquidGlass)  
**Estado**: 🟢 Production Ready (Abril 1, 2026)

## Endpoints disponibles

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/health` | Estado del servidor y Odoo |
| `GET /api/estado-resultados` | Estado de resultados del mes actual |
| `GET /api/gastos-empresa` | Historial de gastos operativos |
| `GET /api/gastos-personales` | Gastos personales |
| `GET /api/ventas-detalle` | Detalle de órdenes de venta |
| `GET /docs` | Documentación interactiva (Swagger UI) |

---

## Seguridad

- El cliente Odoo **solo usa operaciones de lectura** (`search_read`, `read_group`, `search_count`).  
- Cualquier intento de llamar `write`, `create` o `unlink` lanza un error en Python **antes** de hacer ninguna petición de red.  
- La API Key se guarda en `.env` (excluido de Git).
