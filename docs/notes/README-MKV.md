# 📦 Scriptum - Extração de Legendas MKV

Sistema completo para extrair legendas de ficheiros MKV.

## ✅ O Que Foi Implementado

### Backend Python
- ✅ `mkv/subtitle_extractor.py` - Módulo de extração de legendas MKV
  - Detecção automática de tracks de legendas
  - Suporte para múltiplos codecs (SRT, SSA, ASS, PGS, VobSub, WebVTT)
  - Extração individual ou em lote
  - Conversão automática para SRT
- ✅ `api_server_simple.py` - Endpoints HTTP para MKV
  - `/api/mkv/analyze` - Analisa ficheiro MKV e lista tracks
  - `/api/mkv/extract` - Extrai tracks selecionadas

### Frontend JavaScript
- ✅ `mkv-extractor.js` - Interface de utilizador
  - Upload de ficheiros MKV
  - Listagem de tracks com flags de idioma
  - Seleção múltipla de tracks
  - Progress indicator durante extração
  - Integração com sistema de tradução

### Interface HTML/CSS
- ✅ Interface moderna com glassmorphism
- ✅ Cards interativos para cada track
- ✅ Badges para tracks padrão
- ✅ Emojis de bandeiras por idioma
- ✅ Animações suaves

## 🚀 Como Usar

### 1. Iniciar o Servidor

```bash
python3 api_server_simple.py
```

O servidor inicia em `http://localhost:8080`

### 2. Abrir a Aplicação

Abra `index.html` no browser.

### 3. Carregar Ficheiro MKV

1. Clique na área de upload
2. Selecione um ficheiro `.mkv`
3. Clique em "🔍 Analisar Legendas"

### 4. Selecionar Tracks

A aplicação mostra todas as tracks de legendas disponíveis:

```
🇬🇧 Inglês [SRT] ⭐ Padrão
   Track ID: 3

🇵🇹 Português [SRT]
   Track ID: 4

🇪🇸 Espanhol [SSA]
   Nome: Spanish (Castilian)
   Track ID: 5
```

- ⭐ indica a track padrão (selecionada automaticamente)
- Bandeiras emoji identificam o idioma
- Codec tipo (SRT, SSA, ASS, etc.)

### 5. Extrair Legendas

1. Selecione as tracks desejadas (checkboxes)
2. Clique em "Extrair X Tracks"
3. Aguarde a extração
4. Ficheiros SRT são salvos automaticamente

### 6. Traduzir (Opcional)

Após extração, a aplicação pergunta:
```
✅ 2 ficheiro(s) extraído(s) com sucesso!

Deseja traduzir estas legendas agora?
```

- **Sim**: Carrega primeira legenda no tradutor
- **Não**: Ficheiros ficam disponíveis para uso posterior

## 📋 Estrutura de Dados

### Resposta de `/api/mkv/analyze`

```json
{
  "success": true,
  "filename": "movie.mkv",
  "count": 3,
  "tracks": [
    {
      "id": 3,
      "codec": "SRT",
      "language": "eng",
      "name": "English",
      "is_default": true
    },
    {
      "id": 4,
      "codec": "SRT",
      "language": "por",
      "name": "Portuguese",
      "is_default": false
    }
  ]
}
```

### Resposta de `/api/mkv/extract`

```json
{
  "success": true,
  "count": 2,
  "output_dir": "/tmp/scriptum_subs_abc123/",
  "extracted_files": [
    {
      "path": "/tmp/scriptum_subs_abc123/movie_track3.srt",
      "size": 52480,
      "name": "movie_track3.srt"
    },
    {
      "path": "/tmp/scriptum_subs_abc123/movie_track4.srt",
      "size": 48960,
      "name": "movie_track4.srt"
    }
  ]
}
```

## 🔧 Tecnologias Utilizadas

### Backend
- **mkvtoolnix** - Suite de ferramentas MKV
  - `mkvmerge` - Análise de ficheiros MKV
  - `mkvextract` - Extração de tracks
- **Python 3.13+** - Servidor HTTP
  - Parse manual de multipart/form-data (cgi module removido)
  - Tempfile para gestão de ficheiros temporários

### Frontend
- **JavaScript ES6+** - Lógica de interface
- **Fetch API** - Comunicação com servidor
- **FormData** - Upload de ficheiros
- **CSS Glassmorphism** - Estilo moderno

## 📝 Codecs Suportados

| Codec ID | Nome | Formato | Extração |
|----------|------|---------|----------|
| S_TEXT/UTF8 | SRT | SubRip | ✅ Direto |
| S_TEXT/SSA | SSA | SubStation Alpha | ✅ Direto |
| S_TEXT/ASS | ASS | Advanced SSA | ✅ Direto |
| S_HDMV/PGS | PGS | Presentation Graphic Stream | ✅ Imagem |
| S_VOBSUB | VobSub | VOB Subtitles | ✅ Imagem |
| S_TEXT/WEBVTT | WebVTT | Web Video Text Tracks | ✅ Direto |

## 🎯 Fluxo Completo

```
1. Upload MKV
   ↓
2. Análise (mkvmerge -J)
   ↓
3. Listagem de Tracks
   ↓
4. Seleção pelo Utilizador
   ↓
5. Extração (mkvextract tracks)
   ↓
6. Ficheiros SRT salvos
   ↓
7. [Opcional] Carregar no Tradutor
   ↓
8. [Opcional] Buscar Metadados TMDB
   ↓
9. [Opcional] Traduzir com Gemini
```

## ⚠️ Notas Importantes

### Ficheiros Temporários
- MKV é salvo temporariamente para análise/extração
- Ficheiros são apagados após processamento
- Legendas extraídas ficam em `/tmp/scriptum_subs_*/`

### Limitações
- Apenas legendas baseadas em texto (SRT, SSA, ASS, WebVTT)
- Legendas gráficas (PGS, VobSub) são extraídas mas não são texto
- Tamanho máximo de upload depende da configuração do servidor

### Segurança
- Ficheiros são processados em diretórios temporários isolados
- Multipart form data com validação
- CORS habilitado para desenvolvimento local

## 🔍 CLI de Teste

Para testar a extração via linha de comandos:

```bash
python3 mkv/subtitle_extractor.py movie.mkv
```

Output:
```
🔍 Analisando ficheiro MKV: movie.mkv
   ✅ Track 3: eng (SRT)
   ✅ Track 4: por (SRT)
   ✅ Track 5: spa (SSA)

📊 Total: 3 track(s) de legendas encontradas

📋 Tracks disponíveis:
   ⭐ [1] Track 3: eng (SRT)
      [2] Track 4: por (SRT)
      [3] Track 5: spa (SSA)

❓ Quais tracks deseja extrair? (ex: 1,3 ou 'all' para todas)
   Escolha: all

🚀 Extraindo 3 track(s)...

📤 Extraindo track 3 para: movie_track3.srt
   ✅ Legendas extraídas (52480 bytes)

📤 Extraindo track 4 para: movie_track4.srt
   ✅ Legendas extraídas (48960 bytes)

📤 Extraindo track 5 para: movie_track5.srt
   ✅ Legendas extraídas (51200 bytes)

✅ 3/3 tracks extraídas com sucesso

✅ Ficheiros extraídos:
   📄 movie_track3.srt
   📄 movie_track4.srt
   📄 movie_track5.srt

❓ Deseja traduzir estas legendas?
   (s/n):
```

## 🐛 Troubleshooting

### Erro: "mkvmerge not found"
```bash
brew install mkvtoolnix
```

### Erro: "No module named 'cgi'" (Python 3.13+)
O módulo `cgi` foi removido. A aplicação usa parse manual de multipart/form-data.

### Servidor não inicia na porta 8080
```bash
# Verificar processos na porta
lsof -ti:8080

# Matar processo
kill -9 $(lsof -ti:8080)

# Reiniciar servidor
python3 api_server_simple.py
```

---

**Última atualização:** 2026-01-30
**Status:** ✅ Funcional e testado
**Versão:** 1.0.0
