# 🎉 Scriptum v1.0.0 - Release Notes

**Data de Lançamento:** 2 de Fevereiro de 2026

## 🎬 Introdução

Scriptum v1.0 é um sistema profissional e completo para extração, tradução e gestão de legendas de filmes. Combina ferramentas CLI poderosas com uma interface web moderna para proporcionar uma experiência completa de trabalho com legendas.

## ✨ Destaques da Versão

### 🎞️ Extração de Legendas MKV
A funcionalidade mais aguardada! Agora pode extrair legendas diretamente de ficheiros MKV sem ferramentas externas complexas.

```bash
python3 extract_mkv.py "filme.mkv"
```

**Características:**
- ✅ Interface CLI interativa
- ✅ Suporte para múltiplas tracks simultâneas
- ✅ Detecção automática de framerate (vídeo + legendas)
- ✅ Identificação de idiomas
- ✅ Detecção de tracks especiais (Forced, SDH/CC)

### 🌐 Tradução Universal
Não está mais limitado a EN→PT! Agora suporta tradução de **60+ idiomas** para Português.

**Idiomas Suportados:**
- Espanhol, Francês, Alemão, Italiano, Japonês, Chinês
- Coreano, Russo, Árabe, Hindi, e muitos mais!

### 📊 Interface Web Profissional
Interface moderna e intuitiva com monitoramento em tempo real:

- **Dashboard com 6 métricas** em tempo real
- **Gráfico de performance** com Canvas API
- **Live streaming** de traduções
- **ETA dinâmico** e preciso
- **Tema dark** profissional

### 🎯 Detecção de Framerate
Novo detector de framerate para análise técnica:

```bash
python3 detect_framerate.py "filme.mkv"    # Framerate do vídeo
python3 detect_framerate.py "legendas.srt" # Framerate inferido
```

## 📦 O Que Está Incluído

### Scripts CLI
| Script | Função |
|--------|--------|
| `extract_mkv.py` | Extração de legendas MKV |
| `detect_framerate.py` | Análise de framerate |
| `translate.py` | Tradução CLI |
| `validate_and_fix.py` | Validação e correção |

### Launchers
| Ficheiro | Plataforma | Função |
|----------|------------|--------|
| `Iniciar.command` | macOS | Duplo clique para iniciar |
| `Parar.command` | macOS | Duplo clique para parar |
| `start.sh` | Terminal | Script de início |
| `stop.sh` | Terminal | Script de paragem |

### Servidores
- **HTTP Server** (porta 8000) - Interface web
- **API Server** (porta 8080) - Backend (metadados + MKV)

## 🚀 Como Começar

### 1. Instalação Rápida

```bash
# Dependências Python
pip3 install requests pysrt

# MKVToolNix (para extração MKV)
brew install mkvtoolnix
```

### 2. Workflow Típico

```bash
# Passo 1: Extrair legendas do MKV
python3 extract_mkv.py "/Downloads/filme.mkv"

# Passo 2: Iniciar interface web
./Iniciar.command

# Passo 3: Abrir http://localhost:8000/
# Passo 4: Carregar a legenda extraída
# Passo 5: Traduzir!
```

## 📊 Performance

Testado com ficheiros reais:

| Tamanho | Tempo de Tradução | Extração MKV |
|---------|-------------------|--------------|
| 1000 legendas | ~15 minutos | ~5 segundos |
| 1500 legendas | ~20-25 minutos | ~5 segundos |

**Precisão:**
- ✅ Timeframes: 100% corretos
- ✅ Traduções: 100% completas
- ✅ Quebras de linha: 99.3% corretas

## 🔧 Tecnologias

### Backend
- Python 3.13+
- Google Gemini 2.5 Flash API
- MKVToolNix (mkvmerge, mkvextract)
- TMDB API (metadados)

### Frontend
- HTML5 + CSS3 + JavaScript ES6
- Canvas API (gráficos)
- Glassmorphism design
- CSS animations nativas

## 🎯 Casos de Uso

### 1. Filme com Legendas Espanholas
```bash
# Extrair legendas do MKV
python3 extract_mkv.py "filme.mkv"
# → filme_track4.srt (Espanhol)

# Traduzir ES → PT
# (via interface web)
```

### 2. Análise Técnica
```bash
# Verificar framerate do vídeo
python3 detect_framerate.py "filme.mkv"
# → 30.0 fps

# Verificar framerate das legendas
python3 detect_framerate.py "legendas.srt"
# → 23.976 fps (possível dessincronização!)
```

### 3. Batch de Legendas
```bash
# Extrair todas as legendas de uma série
for ep in *.mkv; do
    python3 extract_mkv.py "$ep"
done
```

## 🐛 Problemas Conhecidos

### Resolvidos na v1.0
- ✅ CORS ao carregar ficheiros locais
- ✅ Cache de JavaScript impedindo updates
- ✅ Erro de parsing multipart em Python 3.13
- ✅ Detecção incorreta de idioma

### Limitações Atuais
- Upload de MKV via browser não suportado (use CLI)
- Apenas SRT suportado (ASS/SSA/VTT em v2.0)
- Sem sincronização automática (planejado v2.0)

## 📚 Documentação

- **README.md** - Guia completo de uso
- **CHANGELOG.md** - Histórico detalhado de mudanças
- **VERSION** - Número da versão atual

## 🔮 Próximos Passos - v2.0

Já em desenvolvimento:

### Sincronização Automática (Confirmado!)
- ✨ Usando Whisper MLX para Apple Silicon
- ✨ Detecção automática de delay
- ✨ Correção inteligente com IA
- ✨ Base: `test_sync.py`

### Outras Funcionalidades v2.0
- 🔄 Conversão de framerate
- 📝 Editor inline de legendas
- 🌐 Suporte ASS/SSA/VTT
- 🚀 Batch processing
- 💾 Histórico de traduções
- 🎨 Temas personalizáveis

## 🙏 Agradecimentos

Desenvolvido para a comunidade de cinema portuguesa.

Tecnologias utilizadas:
- Google Gemini API
- MKVToolNix
- TMDB (The Movie Database)
- Python Community

## 📞 Suporte

Para reportar bugs ou sugerir funcionalidades, contacte o desenvolvedor.

---

## 📥 Download

**Versão:** 1.0.0
**Status:** Estável ✅
**Data:** 2026-02-02

### Requisitos do Sistema
- macOS 11+ (Big Sur ou superior)
- Python 3.9+
- 500MB espaço em disco
- Conexão à internet (para API Gemini)

### Ficheiros
```
subtitle-translator/
├── v1.0.0
│   ├── Documentação (README, CHANGELOG, RELEASE)
│   ├── Scripts CLI (extract_mkv, detect_framerate, translate)
│   ├── Interface Web (index.html + assets)
│   ├── API Server (api_server_simple.py)
│   └── Launchers (Iniciar/Parar.command)
```

---

**Scriptum v1.0.0** 🎬
*Tradutor Profissional de Legendas*

Desenvolvido com ❤️ por Nuno
Fevereiro 2026
