# Scriptum (subtitle-translator) - Project Overview

> Esta analise foi feita por inspecao de codigo e docs locais. Nao executei testes nem rodei a app.

## 1. Visao Geral
Scriptum e um conjunto de ferramentas para:
- sincronizacao automatica de legendas com MLX Whisper (Apple Silicon)
- traducao de legendas via Google Gemini
- pesquisa/download de legendas via OpenSubtitles
- reconhecimento de filmes via TMDB
- analise e conversao de video (FFmpeg/FFprobe)

O repo inclui:
- Backend Flask legacy (v2.0/2.1) em `sync_api.py`
- Backend Flask refatorado (v2.1) em `app_refactored.py` + `api/services/*`
- Frontend web legacy (HTML/JS) em `sync.html` + `sync.js`
- Frontend React (Vite) em `frontend/`
- CLI scripts para sincronizacao/ajustes/validacoes
- Um servidor separado de metadados em `api_server.py`

## 2. Arquitetura Atual (Confirmado no codigo)

### 2.1 Backend principal (legacy v2.0/2.1)
Arquivo: `sync_api.py`
- Flask + CORS
- Endpoints (confirmado no codigo):
  - `GET /health`
  - `POST /sync`
  - `POST /search-subtitles`
  - `POST /download-subtitle`
  - `POST /recognize`
  - `POST /analyze-video`
  - `POST /quick-subtitle-search`
  - `POST /extract-mkv-subtitles`
  - `POST /remux-mkv-to-mp4`
  - `POST /convert-to-mp4`
- Implementa:
  - analise de video (ffprobe)
  - reconhecimento TMDB
  - pesquisa OpenSubtitles (hash e query)
  - extracao de legendas de MKV
  - remux e conversao para MP4
  - sincronizacao usando `smart_sync.py`

### 2.2 Backend refatorado (v2.1 - service oriented)
Arquivos: `app_refactored.py` + `api/services/*`
- Flask + CORS
- Servicos:
  - `VideoService` em `api/services/video_service.py`
  - `MovieService` em `api/services/movie_service.py`
  - `SubtitleService` em `api/services/subtitle_service.py`
  - `TranslationService` em `api/services/translation_service.py`
  - `SyncService` em `api/services/sync_service.py`
- Endpoints (confirmado no codigo):
  - `GET /health`
  - `POST /analyze-video`
  - `POST /recognize-movie`
  - `POST /remux-mkv-to-mp4`
  - `POST /convert-to-mp4`
  - `POST /extract-mkv-subtitles`
  - `POST /search-subtitles`
  - `POST /download-subtitle`
  - `POST /sync`
  - `POST /translate`
- Serve `sync.html` diretamente na rota `/`
- Configuracoes centralizadas em `api/config.py`

### 2.3 Servidor de metadados (separado)
Arquivo: `api_server.py`
- Flask + CORS
- Endpoints:
  - `GET /api/health`
  - `GET /api/metadata?filename=...`
  - `GET /api/metadata/search?title=...&year=...`
- Usa `metadata/movie_metadata_manager.py`

### 2.4 Frontend legacy (HTML + JS)
Arquivos: `sync.html`, `sync.js`, `style.css`
- Fluxo de upload de video/legenda
- Player de video com preview e offset manual
- Busca de filme (TMDB) e legenda (OpenSubtitles)
- Sincronizacao automatica (MLX Whisper) via `sync_api.py`
- Conversao/remux MKV -> MP4 e extracao de legendas

### 2.5 Frontend React (Vite)
Diretorio: `frontend/`
- Rotas confirmadas em `frontend/src/router.tsx`:
  - `/` Dashboard
  - `/subtitles/search`
  - `/translate`
  - `/sync`
- Cliente API em `frontend/src/services/api.ts` (consome o backend refatorado)
- Hooks de dominio em `frontend/src/hooks/*`
- Componentes UI em `frontend/src/components/*`

## 3. Funcionalidades (verificadas por codigo)

### 3.1 Sincronizacao de legendas (MLX Whisper)
- Legacy: `sync_api.py` chama funcoes de `smart_sync.py`
- Refatorado: `api/services/sync_service.py` encapsula fluxo
- Caracteristicas:
  - deteccao de framerate do video e inferencia de framerate do SRT
  - conversao de framerate quando necessario
  - extracao de audio via FFmpeg
  - transcricao via MLX Whisper
  - calculo de offsets e aplicacao

### 3.2 Pesquisa e download de legendas
- Legacy: `sync_api.py` integra `opensubtitles_api.py`
- Refatorado: `api/services/subtitle_service.py`
- Metodos:
  - pesquisa por query (nome do filme)
  - pesquisa por hash (quando video disponivel)
  - download por file_id

### 3.3 Reconhecimento de filme (TMDB)
- Legacy: `sync_api.py` (extraicao por regex + chamada TMDB)
- Refatorado: `api/services/movie_service.py` (parse do filename + TMDB)
- Servidor separado: `api_server.py` + `metadata/*`

### 3.4 Analise de video
- Legacy: `sync_api.py` -> `ffprobe`
- Refatorado: `api/services/video_service.py`
- Retorna: formato, tamanho, resolucao, duracao, codec, fps

### 3.5 Conversao/Remux para MP4
- Legacy: `sync_api.py` tem `/remux-mkv-to-mp4` e `/convert-to-mp4`
- Refatorado: `api/services/video_service.py`

### 3.6 Extracao de legendas embutidas (MKV)
- Legacy: `sync_api.py` em `/extract-mkv-subtitles`
- Refatorado: `VideoService.extract_mkv_subtitles`

### 3.7 Traducao de legendas (Gemini)
- Refatorado: `api/services/translation_service.py` usa `translate.py`
- `translate.py`:
  - parse SRT
  - traduz por lotes
  - valida quebras de linha
  - aplica correcoes quando necessario

### 3.8 Utilitarios e scripts CLI
Scripts em raiz (nao exaustivo):
- `smart_sync.py` (sync com framerate)
- `sync_subtitles.py` (sync basico)
- `auto_sync.py`, `full_resync.py`, `fix_sync.py`, `fix_both_offsets.py`
- `detect_framerate.py`, `detect_all_offsets.py`
- `validate_and_fix.py`, `validate-lines.js`
- `extract_mkv.py`, `merge_subtitles.py`
- `translate.py` (CLI de traducao)

## 4. Frontend React - funcionalidades confirmadas

### 4.1 Dashboard (`frontend/src/pages/Dashboard.tsx`)
- Upload de video
- Analise de video via `/analyze-video`
- Reconhecimento de filme via `/recognize-movie`
- Acoes rapidas para pesquisa, traducao e sincronizacao

### 4.2 Pesquisa de legendas (`frontend/src/pages/SubtitleSearch.tsx`)
- Pesquisa por query via `/search-subtitles`
- Download via `/download-subtitle`

### 4.3 Traducao (`frontend/src/pages/TranslationPage.tsx`)
- Upload de SRT
- Selecao de idioma origem/destino
- Chama `/translate`
- Barra de progresso simulada no frontend

### 4.4 Sincronizacao (`frontend/src/pages/SyncPage.tsx`)
- Upload de video + legenda
- Selecao de modelo e idioma (apenas UI)
- Chama `/sync`
- Progresso simulado

## 5. Configuracao e Variaveis de Ambiente

### 5.1 Backend refatorado
Arquivo: `api/config.py`
- `TMDB_API_KEY`
- `OPENSUBTITLES_API_KEY`
- `GEMINI_API_KEY`
- `HOST`, `PORT`, `DEBUG`
- `MAX_VIDEO_SIZE`, `TRANSLATION_BATCH_SIZE`

### 5.2 Arquivo `.env`
- Existe `./.env` e `./.env.example`

## 6. Scripts de Inicializacao
- `start_refactored.sh` inicia `app_refactored.py`
- `start_sync_web.sh` inicia `sync_api.py` e abre `sync.html`
- `start_server.sh` e `start.sh` (nao validados em detalhe)

## 7. Inconsistencias e lacunas encontradas

### 7.1 Frontend React
- Hooks chamam `api.downloadBlob`, mas `ApiClient` nao expõe esse metodo.
  - Referencias: `frontend/src/hooks/useSync.ts`, `useVideo.ts`, `useSubtitle.ts`, `useTranslation.ts`
  - Implementacao existente em `frontend/src/lib/utils.ts` (funcao `downloadBlob`).

### 7.2 Frontend React vs Backend
- `TranslationPage` envia opcoes `tone` e `preserveFormatting`, mas `useTranslation` ignora esses campos e o backend nao os aceita.
- `SyncPage` permite escolher `model` e `language`, mas o backend refatorado nao aceita esses parametros.

### 7.3 Duplicacao de backends
- Existem dois backends principais (`sync_api.py` e `app_refactored.py`) com features sobrepostas, mas nao identicas.
  - O frontend React esta alinhado com `app_refactored.py`.
  - O frontend legacy esta alinhado com `sync_api.py`.

### 7.4 Dependencias
- Nao encontrei `requirements.txt` na raiz. Os scripts de start assumem que existe (ou pedem instalar manualmente dependencias).

## 8. Estrutura do Repositorio (mapa rapido)

- `sync_api.py` - API legacy principal
- `app_refactored.py` - API refatorada
- `api/` - configuracao e servicos modulares
- `frontend/` - app React + Vite
- `sync.html`, `sync.js`, `style.css` - UI legacy
- `translate.py` - tradutor Gemini
- `smart_sync.py` - sincronizacao com framerate
- `metadata/` - sistema de metadados (TMDB + glossario)
- `api_server.py` - servidor de metadados
- `mkv/` - extracao de MKV
- `static/` - assets

## 9. Como rodar (confirmado nos scripts)

### Legacy (sync.html + sync_api.py)
- `./start_sync_web.sh`
- Abre `sync.html` e inicia backend em `http://localhost:5001`

### Refatorado (API + sync.html servido pelo Flask)
- `./start_refactored.sh`
- Servidor em `http://localhost:5001/`

## 10. Riscos e observacoes rapidas
- Muitos endpoints lidam com uploads grandes e subprocessos longos. Isto pode exigir limites e timeouts consistentes.
- CORS esta aberto nos servidores (dev-friendly, risco se exposto publicamente).

---

## 11. Proximos passos sugeridos (opcional)
1. Decidir se o foco e no backend legacy ou no refatorado, e consolidar.
2. Alinhar frontend React com backend (metodos que faltam e parametros ignorados).
3. Criar `requirements.txt`/`pyproject.toml` para dependencias.

