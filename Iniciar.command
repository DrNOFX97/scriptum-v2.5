#!/bin/bash
# 🎬 Subtitle Translator - Complete Startup Script
# Inicia ambos os servidores (HTTP + API) e abre a aplicação

# Ir para o diretório do script
cd "$(dirname "$0")"

echo "🎬 Subtitle Translator - Scriptum"
echo "=================================="
echo ""

# Portas
HTTP_PORT=8000
API_PORT=8080

# Limpar portas se estiverem em uso
echo "🔄 Verificando portas..."
if lsof -Pi :$HTTP_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   Limpando porta $HTTP_PORT..."
    lsof -ti:$HTTP_PORT | xargs kill -9 2>/dev/null
fi

if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   Limpando porta $API_PORT..."
    lsof -ti:$API_PORT | xargs kill -9 2>/dev/null
fi

sleep 1
echo "   ✅ Portas limpas"
echo ""

# Iniciar servidor HTTP (interface)
echo "🌐 Iniciando servidor HTTP (porta $HTTP_PORT)..."
python3 -m http.server $HTTP_PORT > /tmp/scriptum_http.log 2>&1 &
HTTP_PID=$!
sleep 1

if ! lsof -Pi :$HTTP_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   ❌ Erro ao iniciar servidor HTTP"
    read -p "Pressione Enter para sair..."
    exit 1
fi
echo "   ✅ Servidor HTTP iniciado (PID: $HTTP_PID)"

# Iniciar servidor API Python (extração de MKV)
echo "🐍 Iniciando servidor API (porta $API_PORT)..."
python3 api_server_simple.py > /tmp/scriptum_api.log 2>&1 &
API_PID=$!
sleep 2

if ! lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   ❌ Erro ao iniciar servidor API"
    echo "   Verifique os logs em: /tmp/scriptum_api.log"
    read -p "Pressione Enter para sair..."
    exit 1
fi
echo "   ✅ Servidor API iniciado (PID: $API_PID)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Todos os servidores iniciados!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Interface:  http://localhost:$HTTP_PORT/"
echo "📍 API:        http://localhost:$API_PORT/"
echo ""
echo "🌐 Abrindo navegador..."

# Abrir no navegador
open "http://localhost:$HTTP_PORT/"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ℹ️  Informações:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PIDs dos servidores:"
echo "  • HTTP: $HTTP_PID"
echo "  • API:  $API_PID"
echo ""
echo "Para parar tudo:"
echo "  • Executar: Parar.command"
echo "  • Ou terminal: kill $HTTP_PID $API_PID"
echo ""
echo "Logs:"
echo "  • HTTP: /tmp/scriptum_http.log"
echo "  • API:  /tmp/scriptum_api.log"
echo ""
echo "Pressione Enter para fechar (servidores continuarão rodando)"
read
