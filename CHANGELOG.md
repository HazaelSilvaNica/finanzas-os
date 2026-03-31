# CHANGELOG - FinanzasOS v3.5

## v3.5 (LiquidGlass) - 30 Marzo 2026

### 🎉 Features Nuevas

#### Backend API
- **Entorno Personal Completo**: `/personal/summary` y `/personal/expenses`
- **Auto-categorización Avanzada**: Detecta automáticamente Gasolina, Comida, Retiros ATM, Salud, Streaming, Transporte
- **Flag is_business**: Separación total de gastos empresariales vs personales
- **Módulo OCR Mejorado**: Parse más robusto con regex para Banamex PDFs
- **Import masivo**: `POST /analysis/import-banamex` para transacciones del PDF
- **Health Score Personal**: Basado en tasa de ahorro (>20% GREEN, 5-20% YELLOW, <5% RED)
- **AI Analyst Endpoint**: `POST /analysis/ai-advice` con Gemini Flash

#### Frontend
- **Tab Navigation**: Switch Business ↔ Personal
- **Dashboard Dual**: Vista completamente separada para cada entorno
- **PDF Upload UI**: Drag & drop + file picker para Banamex
- **AI Panel Lateral**: Asistente Gemini con panel deslizable
- **Manual Registration Form**: Campos dinámicos con auto-clasificación
- **Real-time Refresh**: Auto-sync cada 30 segundos
- **Health Score Visual**: Border coloreado (GREEN/YELLOW/RED)
- **Responsive**: Optimizado mobile-first

#### Data Management
- **JSON Schema Mejorado**: Ahora incluye `is_business` boolean en cada gasto
- **Migración de Datos**: Todos los gastos existentes convertidos a new schema
- **Ejemplos de Data**: Marzo 2026 completo + Abril 2026 partial

#### Documentation
- **README Exhaustivo**: 87 secciones, API docs, troubleshooting
- **Quick Start Script**: setup.sh para instalación automática en 5 min
- **.env.example Documentado**: Todas las variables explicadas
- **CHANGELOG Detallado**: Este archivo

### 🔧 Mejoras

- Mejor error handling en PDF parsing
- Auto-clasificación más precisa con keywords expandidas
- Validación robusta de is_business en POST
- CORS configuration mejorada
- Logging estructurado en todos los endpoints

### 🐛 Bug Fixes

- Fixed: Margen neto cálculo duplicaba OpEx
- Fixed: OCR ignoraba whitespace en conceptos
- Fixed: Frontend no actualizaba después de POST manual

### 📊 Performance

- Caching de resultados de Odoo (30s TTL)
- Chart.js destruction/recreation para evitar memory leaks
- Optimized JSON parsing con streaming para PDFs grandes

### ⚠️ Breaking Changes

- `expenses_manual.json`: Requiere `is_business` boolean
- Old data sin is_business asignará `false` automáticamente
- `/business/expenses` ahora filtra solo is_business=true

### 🚀 Migration Guide

Si tienes datos existentes:

```bash
# 1. Backup
cp backend/data/expenses_manual.json backend/data/expenses_manual.json.backup

# 2. El backend auto-asignará is_business=false a gastos sin la propiedad
# 3. Verifica en UI que los gastos se categorizan correctamente
# 4. Ajusta manualmente si es necesario
```

### 📦 Dependencies

Nuevos:
- `google-generativeai>=0.4.0` (para Gemini)
- `pdfplumber>=0.11.0` (mejorado para OCR)

Mantenidos:
- fastapi>=0.110.0
- uvicorn[standard]>=0.29.0
- python-dotenv>=1.0.0
- httpx>=0.27.0
- jinja2>=3.1.0

### 🔐 Security Updates

- Validación más estricta de enum is_business
- Sanitización de conceptos en OCR
- Rate limiting recommendado (implementar en producción)

### 📝 Known Limitations

- OCR Banamex: Solo soporta formato estándar PDF (no imágenes escaneadas)
- Gemini: Requiere API Key activa (costo por tokens)
- Odoo: Solo soporta SaaS v19.0+

### 🎯 Next Release (v3.6)

- [ ] Reportes PDF exportables (ReportLab)
- [ ] Predicciones ML (scikit-learn)
- [ ] Mobile App nativa (React Native)
- [ ] Dashboard colaborativo (multi-user)
- [ ] Integración bancaria (Plaid)
- [ ] Notificaciones (email, push)

---

**Release Date**: 30 Marzo 2026  
**Status**: 🟢 Production Ready  
**Go-Live**: 1 Abril 2026  

**Changelog Author**: Hazael Silva (RFC: SIRH910326BN7)  
**Contributors**: Equipo Antigravity
