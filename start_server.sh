#!/bin/bash
# Scriptum API Server Launcher

echo "🚀 Iniciando Scriptum API Server..."

# Limpar porta 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Iniciar servidor
python3 -u api_server_simple.py 2>&1 | tee server.log
