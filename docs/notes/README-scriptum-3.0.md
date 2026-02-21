# Scriptum 3.0

Nova interface profissional para tradução, edição e sincronização de legendas.

## Objetivo
- Prioridade: tradução de legendas
- Secundário: edição e sincronização automática
- Integração total num único workspace

## Como usar
1. Iniciar o backend refatorado:
   - `./start_refactored.sh`
2. Abrir a interface:
   - `scriptum 3.0/index.html`

## Requisitos
- Backend ativo em `http://localhost:5001` (configurável em Settings)
- FFmpeg/FFprobe instalados para ferramentas de vídeo

## Funcionalidades
- Tradução com contexto
- Edição com renumeração, normalização e offset global
- Sincronização automática com MLX Whisper
- Pesquisa e download de legendas
- Análise de vídeo e ferramentas de conversão

## Notas
- Esta versão é independente e não altera a v2.0
- Configurações ficam guardadas no localStorage
