#!/bin/bash
# 🛑 Subtitle Translator - Stop Script
# Para o servidor HTTP

echo "🛑 A parar Subtitle Translator..."
echo ""

PORT=8000

# Verificar se há servidor rodando
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "🔍 Encontrado servidor na porta $PORT"
    PID=$(lsof -ti:$PORT)
    echo "📍 PID: $PID"
    echo "🔄 Matando processo..."

    kill -9 $PID 2>/dev/null

    sleep 1

    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "❌ Erro ao parar servidor"
        exit 1
    else
        echo "✅ Servidor parado com sucesso!"
    fi
else
    echo "ℹ️  Nenhum servidor rodando na porta $PORT"
fi

echo ""
