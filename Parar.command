#!/bin/bash
# 🛑 Subtitle Translator - Stop All Servers
# Para ambos os servidores (HTTP + API)

# Ir para o diretório do script
cd "$(dirname "$0")"

echo "🛑 A parar Subtitle Translator..."
echo "================================"
echo ""

HTTP_PORT=8000
API_PORT=8080
STOPPED=0

# Parar servidor HTTP
if lsof -Pi :$HTTP_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "🌐 Parando servidor HTTP (porta $HTTP_PORT)..."
    PID=$(lsof -ti:$HTTP_PORT)
    echo "   PID: $PID"
    kill -9 $PID 2>/dev/null
    sleep 1

    if lsof -Pi :$HTTP_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   ❌ Erro ao parar servidor HTTP"
    else
        echo "   ✅ Servidor HTTP parado"
        STOPPED=$((STOPPED + 1))
    fi
else
    echo "ℹ️  Servidor HTTP não está rodando (porta $HTTP_PORT)"
fi

echo ""

# Parar servidor API
if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "🐍 Parando servidor API (porta $API_PORT)..."
    PID=$(lsof -ti:$API_PORT)
    echo "   PID: $PID"
    kill -9 $PID 2>/dev/null
    sleep 1

    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   ❌ Erro ao parar servidor API"
    else
        echo "   ✅ Servidor API parado"
        STOPPED=$((STOPPED + 1))
    fi
else
    echo "ℹ️  Servidor API não está rodando (porta $API_PORT)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $STOPPED -eq 0 ]; then
    echo "ℹ️  Nenhum servidor estava rodando"
elif [ $STOPPED -eq 1 ]; then
    echo "✅ 1 servidor parado"
else
    echo "✅ Todos os servidores parados!"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Pressione Enter para fechar"
read
