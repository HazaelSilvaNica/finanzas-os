#!/bin/bash
# FinanzasOS v3.5 Quick Start Script
# Compatible con macOS, Linux, WSL

set -e

echo "🚀 FinanzasOS v3.5 (LiquidGlass) - Setup Rápido"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo "📦 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no encontrado. Instálalo desde python.org${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# Determine OS
echo ""
echo "🖥️  OS detectado: $(uname -s)"

# Navigate to backend
cd backend

# Create venv
echo ""
echo "🔧 Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ venv creado${NC}"
else
    echo -e "${YELLOW}⚠️  venv ya existe${NC}"
fi

# Activate venv
echo "🔌 Activando venv..."
source venv/bin/activate

# Install requirements
echo ""
echo "📚 Instalando dependencias (pip install -r requirements.txt)..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# Copy .env if not exists
echo ""
echo "⚙️  Configurando .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env creado. IMPORTANTE: Editalo con tus credenciales${NC}"
    echo "   - ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY"
    echo "   - GEMINI_API_KEY (opcional pero recomendado para AI)"
else
    echo -e "${YELLOW}⚠️  .env ya existe${NC}"
fi

# Test imports
echo ""
echo "🧪 Verificando imports..."
python3 -c "import fastapi; import pdfplumber; import google.generativeai" 2>/dev/null && \
    echo -e "${GREEN}✅ Todos los imports OK${NC}" || \
    echo -e "${RED}❌ Falta instalar algo${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Setup completado!${NC}"
echo ""
echo "📋 Próximos pasos:"
echo "1. Edita backend/.env con tus credenciales de Odoo + Gemini"
echo "2. Inicia el backend:"
echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "3. En otra terminal, inicia el frontend:"
echo "   cd frontend && python -m http.server 5173"
echo "4. Abre http://localhost:5173 en tu navegador"
echo ""
echo "💡 Verificar setup:"
echo "   curl http://localhost:8000/api/health"
echo ""
