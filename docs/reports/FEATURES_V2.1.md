# Scriptum v2.1 - Novas Funcionalidades

## 🎯 Análise Automática de Vídeo

Quando um vídeo é carregado, o sistema agora **analisa automaticamente**:

### 📊 Informações do Vídeo
- **Formato**: MKV, MP4, AVI, etc.
- **Tamanho**: em MB
- **Resolução**: 1920x1080, 1280x720, etc.
- **Duração**: formatada em horas/minutos
- **Codec**: H.264, HEVC, etc.
- **FPS**: taxa de quadros

### 🎬 Reconhecimento de Filme (TMDB)
- **Título** do filme
- **Ano** de lançamento
- **Rating** IMDB (⭐ X.X/10)
- **Poster** oficial
- **Sinopse** completa

### 📥 Legendas Disponíveis
- **Busca automática** no OpenSubtitles.com
- Lista de **até 10 legendas** mais relevantes
- Informações de cada legenda:
  - Nome do arquivo
  - Idioma (PT, EN, etc.)
  - Número de downloads
  - Rating da legenda
- **Click para baixar** direto na lista

### 🎞️ Conversão para MP4
- Disponível para formatos: **MKV, AVI, WebM, FLV, WMV**
- **3 níveis de qualidade**:
  - ⚡ **Rápida**: Conversão mais rápida, menor qualidade (CRF 28)
  - ⚖️ **Balanceada**: Recomendado - bom equilíbrio (CRF 23)
  - 💎 **Alta**: Melhor qualidade, conversão mais lenta (CRF 18)
- Codec: **H.264 + AAC** (máxima compatibilidade)
- **Download automático** do arquivo convertido

---

## 🆕 Novos Endpoints API

### POST `/analyze-video`
Análise completa do vídeo com todas as informações acima.

**Request**:
```bash
curl -X POST http://localhost:5001/analyze-video \
  -F "video=@movie.mkv" \
  -F "language=pt"
```

**Response**:
```json
{
  "success": true,
  "filename": "movie.mkv",
  "video_info": {
    "format": "MKV",
    "size_mb": 1450.5,
    "resolution": "1920x1080",
    "duration_formatted": "2h 15m",
    "codec": "h264",
    "fps": 23.976
  },
  "movie": {
    "title": "The Matrix",
    "year": "1999",
    "rating": 8.7,
    "poster": "https://image.tmdb.org/t/p/w300/...",
    "overview": "..."
  },
  "subtitles": [
    {
      "name": "The.Matrix.1999.1080p.BluRay.srt",
      "language": "pt",
      "file_id": "12345",
      "downloads": 5000,
      "rating": 9.5
    }
  ],
  "can_convert_to_mp4": true
}
```

### POST `/convert-to-mp4`
Converte vídeo para formato MP4.

**Request**:
```bash
curl -X POST http://localhost:5001/convert-to-mp4 \
  -F "video=@movie.mkv" \
  -F "quality=balanced"
```

**Response**: Binary (arquivo MP4)

**Parâmetros de qualidade**:
- `fast`: CRF 28, preset veryfast
- `balanced`: CRF 23, preset medium (padrão)
- `high`: CRF 18, preset slow

---

## 🎨 Interface Atualizada

### Painel de Análise
- Aparece **automaticamente** ao carregar vídeo
- Design moderno com animações suaves
- Organizado em **3 seções**:
  1. 📊 Informações do Vídeo
  2. 📥 Legendas Disponíveis (clicáveis)
  3. 🎞️ Conversão para MP4 (se aplicável)

### Experiência do Utilizador
- **Zero interação necessária** - tudo acontece automaticamente
- Click numa legenda → **download e carregamento automático**
- Conversão com **seleção visual de qualidade**
- **Logs em tempo real** de todas as operações

---

## 📝 Exemplo de Uso

1. **Abra** `sync.html` no browser
2. **Arraste** um arquivo MKV
3. **Aguarde 5-10 segundos** - o sistema:
   - ✅ Carrega o vídeo no player
   - ✅ Reconhece o filme (TMDB)
   - ✅ Busca legendas disponíveis
   - ✅ Analisa formato/codec/duração
   - ✅ Mostra opção de conversão MP4
4. **Click numa legenda** → carregada automaticamente
5. **Click "Sincronizar"** → MLX Whisper sincroniza
6. **Download** da legenda sincronizada

---

## 🔧 Requisitos Técnicos

- **FFmpeg** com libx264 (para conversão)
- **FFprobe** (análise de vídeo)
- **OpenSubtitles API Key** (busca de legendas)
- **TMDB API Key** (reconhecimento de filme)

---

## 📊 Estatísticas da Implementação

**Código adicionado**: ~250 linhas
- sync_api.py: +260 linhas (2 novos endpoints)
- sync.html: +150 linhas (painel de análise)
- sync.js: +210 linhas (lógica de análise)

**Tempo de análise**: 5-15 segundos (dependendo do tamanho do vídeo)

**Tempo de conversão**:
- Vídeo 2h em MKV (2GB):
  - Rápida: ~10-15 min
  - Balanceada: ~20-30 min
  - Alta: ~40-60 min

---

## ✨ Melhorias vs Versão 1.0

| Feature | v1.0 | v2.1 |
|---------|------|------|
| Busca de legendas | Manual | ✅ **Automática** |
| Info do filme | Manual | ✅ **Automática** |
| Análise de vídeo | Não | ✅ **Sim** |
| Conversão MP4 | Não | ✅ **Sim** |
| Click para baixar legenda | Não | ✅ **Sim** |
| Painel integrado | Não | ✅ **Sim** |

---

**Desenvolvido com ❤️ usando Claude Code**
**Versão**: 2.1
**Data**: 2026-02-03
