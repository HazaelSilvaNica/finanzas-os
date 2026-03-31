# 🚀 FinanzasOS - Quick Start (5 minutos)

## TL;DR

Una plataforma de gestión financiera que sincroniza Odoo con gastos personales + OCR de Banamex + AI Analyst.

---

## ⚡ Instalación

### macOS / Linux
```bash
cd ./backend
bash ../setup.sh
```

Luego edita `.env` con tus credenciales:
```env
ODOO_URL=https://electriganadero.odoo.com
ODOO_DB=electriganadero
ODOO_LOGIN=tu_email@gmail.com
ODOO_API_KEY=sk_xxxxx  # De Odoo → Avatar → Seguridad
GEMINI_API_KEY=sk_xxxxx  # De Google AI Studio
```

### Windows (Git Bash o WSL)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## ▶️ Run

### Terminal 1 (Backend)
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate en Windows
uvicorn main:app --reload --port 8000
```

### Terminal 2 (Frontend)
```bash
cd frontend
python -m http.server 5173
```

### Abrir
- http://localhost:5173 en el navegador

---

## ✅ Verificar Setup

```bash
curl http://localhost:8000/api/health
```

Debe retornar:
```json
{
  "servidor": "FinanzasOS Backend v1.0",
  "estado": "online",
  "odoo": { "estado": "conectado" }
}
```

---

## 🎯 Flujo Principal

1. **Dashboard** abre con resumen empresarial (Marzo 2026):
   - Ventas: $685,808
   - Compras: $539,120
   - Margen: 13.45% ✅ GREEN

2. **Pestaña Personal**: tus gastos actuales ($10,813.28)

3. **Botón "Asistente IA"**: genera recomendaciones con Gemini

4. **PDF Upload**: carga tu estado Banamex y extrae transacciones

5. **Nuevo Registro**: agrega gasto manual (auto-categorizado)

---

## 📊 API Endpoints

```
GET  /api/v1/business/summary      → Resumen empresarial
GET  /api/v1/business/expenses     → Gastos por categoría
GET  /api/v1/personal/summary      → Resumen personal
GET  /api/v1/personal/expenses     → Gastos personales
POST /api/v1/expenses/manual       → Registra gasto
POST /api/v1/analysis/upload-pdf   → Procesa PDF
POST /api/v1/analysis/import-banamex → Importa transacciones
POST /api/v1/analysis/ai-advice    → Genera recomendaciones
```

---

## 🆘 Problemas Comunes

| Problema | Solución |
|----------|----------|
| **Backend no carga** | Verificar que Python 3.9+ está instalado |
| **Odoo no conecta** | Revisa ODOO_API_KEY en .env (Odoo → Seguridad → Nuevo Token) |
| **AI no funciona** | Agrega GEMINI_API_KEY en .env (https://aistudio.google.com) |
| **PDF no extrae datos** | Asegurar que es PDF válido de Banamex en formato estándar |

---

## 📚 Más Info

- **README.md**: Documentación exhaustiva
- **CHANGELOG.md**: Qué cambió en v3.5
- **http://localhost:8000/docs**: Swagger docs de la API

---

**¿Listo?** Abre http://localhost:5173 y explora FinanzasOS 🎉
