#!/bin/bash
# Scriptum v2.0 - Inicializador Web Interface
# Inicia servidor backend e abre interface web

set -e

echo "=========================================="
echo "🎬 Scriptum v2.0 - Web Interface"
echo "=========================================="
echo ""

# Verificar venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment não encontrado!"
    echo "   Execute: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Verificar dependências
if ! venv/bin/python -c "import flask, flask_cors" 2>/dev/null; then
    echo "📦 Instalando dependências web..."
    venv/bin/pip install flask flask-cors requests
fi

echo "🚀 Iniciando servidor backend..."
echo ""

# Carregar API key do .env se existir
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ API key carregada de .env"
fi

# Iniciar servidor em background
venv/bin/python sync_api.py > /tmp/scriptum_sync.log 2>&1 &
SERVER_PID=$!

echo "   PID: $SERVER_PID"
echo "   Log: /tmp/scriptum_sync.log"
echo ""

# Esperar servidor iniciar
echo "⏳ Aguardando servidor..."
sleep 3

# Verificar se servidor está running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Erro ao iniciar servidor!"
    echo "   Log:"
    cat /tmp/scriptum_sync.log
    exit 1
fi

echo "✅ Servidor iniciado em http://localhost:5001"
echo ""

# Abrir interface web
INTERFACE_FILE="$(pwd)/sync.html"

if [ -f "$INTERFACE_FILE" ]; then
    echo "🌐 Abrindo interface web..."
    open "$INTERFACE_FILE"
    echo ""
    echo "=========================================="
    echo "✅ Sistema pronto!"
    echo "=========================================="
    echo ""
    echo "Interface: file://$INTERFACE_FILE"
    echo "API:       http://localhost:5001"
    echo ""
    echo "⌨️  Pressione CTRL+C para parar"
    echo ""

    # Manter script rodando e mostrar logs
    trap "kill $SERVER_PID 2>/dev/null; echo '\n🛑 Servidor parado'; exit" INT TERM

    tail -f /tmp/scriptum_sync.log
else
    echo "❌ Interface web não encontrada: $INTERFACE_FILE"
    kill $SERVER_PID
    exit 1
fi
