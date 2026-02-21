#!/bin/bash
# 🎬 Subtitle Translator - Startup Script
# Inicia o servidor HTTP e abre a aplicação no navegador

echo "🎬 Subtitle Translator"
echo "====================="
echo ""

# Diretório do projeto
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Porta do servidor
PORT=8000

# Verificar se a porta já está em uso
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Porta $PORT já está em uso"
    echo "🔄 Limpando porta..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# Iniciar servidor HTTP em background
echo "🚀 Iniciando servidor HTTP na porta $PORT..."
python3 -m http.server $PORT > /dev/null 2>&1 &
SERVER_PID=$!

# Aguardar servidor iniciar
sleep 2

# Verificar se o servidor está rodando
if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "❌ Erro ao iniciar servidor"
    exit 1
fi

echo "✅ Servidor iniciado (PID: $SERVER_PID)"
echo ""
echo "📍 URL: http://localhost:$PORT/"
echo ""
echo "🌐 Abrindo navegador..."

# Abrir no navegador
open "http://localhost:$PORT/"

echo ""
echo "✅ Aplicação iniciada com sucesso!"
echo ""
echo "Para parar o servidor:"
echo "  kill $SERVER_PID"
echo "  ou execute: lsof -ti:$PORT | xargs kill"
echo ""
echo "Pressione Ctrl+C para sair (servidor continuará rodando)"
echo ""

# Manter o script rodando para mostrar logs se necessário
# Descomentar a linha abaixo para ver logs em tempo real:
# tail -f /dev/null
