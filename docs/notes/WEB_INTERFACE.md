# 🌐 Scriptum v2.0 - Interface Web

Guia completo da interface web de sincronização de legendas

## 🚀 Início Rápido

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Iniciar interface
./start_sync_web.sh
```

A interface abre automaticamente no navegador em: `file:///Users/.../sync.html`
O servidor backend inicia em: `http://localhost:5001`

## 📋 Funcionalidades

### 1. Upload de Ficheiros

**Vídeo:**
- Formatos suportados: `.mp4`, `.mkv`, `.avi`, `.webm`
- Drag & Drop ou clique para selecionar
- Exibição do nome e tamanho do ficheiro

**Legenda:**
- Formato: `.srt`
- Drag & Drop ou clique para selecionar
- Parsing automático das legendas

### 2. Reconhecimento de Filme (TMDB)

Automático ao carregar o vídeo:
- **Extrai** nome do filme do ficheiro
- **Busca** no TMDB
- **Exibe** poster, título, ano, rating, duração

### 3. Player de Vídeo

- **HTML5 player** com controles nativos
- **Overlay de legendas** em tempo real
- **Sincronização dinâmica** com offset ajustável
- **Pré-visualização** das legendas sincronizadas

### 4. Sincronização Automática

Clique em **"🤖 Sincronizar Automaticamente"**:

1. **Upload** para servidor backend
2. **Análise de framerate** (vídeo e legendas)
3. **Conversão de framerate** se necessário
4. **Extração de áudio** em 5 pontos do filme
5. **Transcrição com Whisper** (MLX - Apple Silicon)
6. **Detecção de idioma** automática
7. **Cálculo de offsets** (média, desvio padrão)
8. **Aplicação da correção**
9. **Download automático** do resultado

**Tempo estimado:** 3-5 minutos (depende do tamanho do vídeo)

### 5. Ajuste Manual

**Slider de Offset:**
- Range: -10s a +10s
- Precisão: 0.1s (100ms)
- Atualização em tempo real no player

**Botões Rápidos:**
- ⏪ -0.5s - Recuar meio segundo
- ⏩ +0.5s - Avançar meio segundo
- ⏪⏪ -5s - Recuar 5 segundos
- ⏩⏩ +5s - Avançar 5 segundos

**Aplicar Ajuste:**
- Clique em **"✅ Aplicar Ajuste Manual"**
- As legendas são ajustadas no player
- Use para refinamento fino após sincronização automática

### 6. Log em Tempo Real

Console de log com 3 níveis:
- 🔵 **INFO** - Informação geral
- ✅ **SUCCESS** - Operações bem-sucedidas
- ❌ **ERROR** - Erros e avisos

Exibe detalhes técnicos:
- FPS do vídeo e legendas
- Idioma detectado
- Duração do filme
- Offsets calculados
- Correções aplicadas

### 7. Download

Clique em **"💾 Download Legenda Sincronizada"**:
- Nome: `{original}.sync.srt`
- Formato: UTF-8
- Timestamps corrigidos com offset aplicado

## 🎨 Interface

### Layout

**Coluna Esquerda (2/3):**
- Player de vídeo
- Informações do filme (IMDB/TMDB)
- Controles de sincronização manual

**Coluna Direita (1/3):**
- Upload de ficheiros
- Botões de ação
- Barra de progresso
- Mensagens de status
- Log console

### Design

- **Tema:** Glassmorphism com gradiente roxo
- **Animações:** Transições suaves
- **Responsivo:** Adapta-se a diferentes resoluções
- **Dark Mode:** Console de log com fundo escuro

## 🔧 Tecnologia

### Frontend
- HTML5 + CSS3 + Vanilla JavaScript
- HTML5 Video API para player
- Fetch API para comunicação com backend
- SRT parsing no browser

### Backend
- Flask (Python)
- Whisper MLX para transcrição
- FFmpeg para extração de áudio
- TMDB API para metadados

## 📊 Fluxo de Trabalho Completo

```
1. UPLOAD
   ↓
   Vídeo + Legenda
   ↓
2. RECONHECIMENTO
   ↓
   TMDB API → Poster, Título, Ano
   ↓
3. SINCRONIZAÇÃO AUTOMÁTICA
   ↓
   Backend:
   - Detecção FPS
   - Conversão FPS (se necessário)
   - Extração áudio (5 pontos)
   - Transcrição Whisper
   - Cálculo offsets
   - Aplicação correção
   ↓
4. PRÉ-VISUALIZAÇÃO
   ↓
   Player com legendas sincronizadas
   ↓
5. AJUSTE MANUAL (opcional)
   ↓
   Slider + Botões rápidos
   ↓
6. DOWNLOAD
   ↓
   {nome}.sync.srt
```

## 🆘 Resolução de Problemas

### Servidor não inicia

```bash
# Verificar se porta 5001 está livre
lsof -i :5001

# Matar processo se necessário
kill -9 <PID>

# Reinstalar dependências
pip install flask flask-cors requests
```

### Erro "CORS blocked"

O servidor Flask já tem CORS habilitado. Se persistir:
1. Verificar se backend está rodando em `http://localhost:5001`
2. Verificar console do browser (F12) para detalhes

### Vídeo não carrega

Formatos suportados pelo HTML5:
- ✅ MP4 (H.264)
- ✅ WebM
- ⚠️ MKV (pode não funcionar em todos os browsers)

**Solução:** Converter MKV para MP4:
```bash
ffmpeg -i input.mkv -c copy output.mp4
```

### Sincronização imprecisa

1. **Verificar fonte do vídeo**
   - Mesmo source que as legendas?
   - TELESYNC vs WEB-DL podem ter edições diferentes

2. **Usar ajuste manual**
   - Sincronização automática: ±2-3s precisão
   - Slider manual: ±0.1s precisão

3. **Tentar diferentes scripts CLI**
   ```bash
   # Mais preciso (iterativo)
   python3 auto_sync.py video.mkv subtitle.srt

   # Com conversão de framerate
   python3 smart_sync.py video.mkv subtitle.srt
   ```

## 🎯 Dicas de Uso

1. **Vídeos grandes**
   - A sincronização pode demorar 5-10 minutos
   - Acompanhe o progresso no log
   - Não feche o browser durante o processo

2. **Múltiplas tentativas**
   - Pode fazer upload e sincronizar novamente
   - Tente diferentes ajustes manuais
   - O original nunca é modificado

3. **Framerate**
   - O sistema detecta e corrige automaticamente
   - 23.976 ↔ 24 fps
   - 25 ↔ 29.97 fps
   - Conversão é sempre aplicada primeiro

4. **Idioma**
   - Detecção automática do áudio
   - Whisper otimizado para inglês
   - Outros idiomas funcionam mas com menos precisão

## 📚 Arquivos da Interface

```
sync.html          → Interface principal (HTML + CSS)
sync.js            → Lógica frontend (JavaScript)
sync_api.py        → Servidor backend (Flask)
start_sync_web.sh  → Script de inicialização
```

## 🔗 Endpoints API

```
GET  /health
     → Status do servidor

POST /sync
     Content-Type: multipart/form-data
     Fields: video, subtitle
     → Sincroniza legendas

POST /recognize
     Content-Type: application/json
     Body: { "filename": "movie.mkv" }
     → Reconhece filme no TMDB
```

## 📝 Notas

- **Apple Silicon:** Whisper MLX otimizado para M1/M2/M3
- **Offline:** Precisa internet apenas para TMDB (opcional)
- **Privacidade:** Tudo é processado localmente
- **Segurança:** Ficheiros temporários são deletados automaticamente

---

**Scriptum v2.0** - Sincronização Inteligente de Legendas 🎬
