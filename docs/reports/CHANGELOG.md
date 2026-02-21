# Changelog - Scriptum

Todas as mudanças notáveis do projeto serão documentadas neste ficheiro.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-02

### 🎉 Lançamento v2.0 - Sincronização Automática com IA

Segunda versão do Scriptum - Adiciona sincronização inteligente de legendas usando IA.

### ✨ Adicionado

#### Sincronização Automática de Legendas (PRINCIPAL)
- Script `sync_subtitles.py` para sincronização automática vídeo-legendas
- Integração com Whisper MLX (otimizado para Apple Silicon)
- Detecção automática de delay/offset entre vídeo e legendas
- Correção adaptativa inteligente:
  - Offset < 1.5s → ajuste simples de timestamps
  - Offset > 1.5s → ffsubsync para sincronização avançada
- Análise rápida usando apenas primeiros 120 segundos
- Extração automática de áudio com FFmpeg
- Transcrição com MLX (aceleração GPU Apple)
- Cálculo de desvio médio entre 40 amostras
- Geração automática de ficheiro .sync.srt

#### Dependências v2.0
- MLX Framework (0.30.4) para aceleração GPU
- mlx-whisper (0.4.3) para transcrição de áudio
- ffsubsync (0.4.31) para sincronização avançada
- pysrt (1.1.2) para manipulação de SRT
- FFmpeg para extração de áudio

### 🔧 Melhorado

- Ambiente virtual Python recomendado para isolamento
- Documentação completa do workflow v2.0
- README com instruções de instalação v2.0
- Exemplos de uso detalhados

### 🚀 Performance

- Sincronização: ~2-3 minutos (120s de áudio)
- Whisper MLX otimizado para Apple Silicon
- Aceleração GPU via MLX Framework

### 📚 Documentação

- README.md atualizado para v2.0
- CHANGELOG.md atualizado
- VERSION atualizado para 2.0.0
- Exemplos de uso de sincronização

### 🎯 Workflow v2.0

```bash
# 1. Extrair legendas
python3 extract_mkv.py "filme.mkv"

# 2. Sincronizar (NOVO!)
source venv/bin/activate
python3 sync_subtitles.py "filme.mkv" "legendas.srt"

# 3. Traduzir
./Iniciar.command
# Interface web → carregar .sync.srt → traduzir
```

---

## [1.0.0] - 2026-02-02

### 🎉 Lançamento Inicial - v1.0

Primeira versão estável do Scriptum - Tradutor Profissional de Legendas.

### ✨ Adicionado

#### Extração de Legendas MKV
- Script `extract_mkv.py` para extração CLI de legendas MKV
- Suporte para múltiplas tracks de legendas
- Interface interativa para seleção de tracks
- Detecção automática de idioma das legendas
- Identificação de tracks padrão, forçadas e SDH

#### Detecção de Framerate
- Script `detect_framerate.py` para análise de framerate
- Detecção de framerate do vídeo MKV via mkvmerge
- Inferência de framerate de legendas SRT por análise de timestamps
- Suporte para framerates comuns: 23.976, 24, 25, 29.97, 30, 50, 59.94, 60 fps

#### Interface Web
- Interface web moderna com design glassmorphism
- Dashboard com 6 métricas em tempo real
- Gráfico de performance com Canvas API
- Live streaming de traduções com rolling automático
- Barra de progresso avançada com ETA dinâmico
- Painel de opções configuráveis
- Tema dark para live stream

#### Tradução
- Tradução automática com Google Gemini 2.5 Flash API
- Suporte para 60+ idiomas (detecção automática)
- Preservação perfeita de timeframes (100%)
- Sistema de retry inteligente para falhas de rede
- Validação automática de traduções
- Correção automática de quebras de linha

#### Metadados de Filmes
- Integração com TMDB (The Movie Database)
- Detecção automática do filme pelo nome do ficheiro
- Exibição de poster, título, ano, géneros, sinopse e elenco
- API key pré-configurada

#### Scripts de Inicialização
- `Iniciar.command` - Launcher para macOS (duplo clique)
- `Parar.command` - Stopper para macOS (duplo clique)
- `start.sh` - Script de início para terminal
- `stop.sh` - Script de paragem para terminal
- Inicialização automática de dois servidores:
  - HTTP Server (porta 8000) - Interface web
  - API Server (porta 8080) - Extração MKV + Metadados

#### Arquitetura
- Servidor HTTP para interface web
- API Server Python para backend
- Sistema modular com separação de responsabilidades
- Scripts CLI standalone para operações específicas

### 🔧 Melhorado

- Sistema de logging aprimorado
- Gestão de erros mais robusta
- Performance otimizada para grandes ficheiros
- Cache-busting para JavaScript (versão 2)
- Interface responsiva e adaptável

### 📦 Dependências

- Python 3.x
- Google Gemini API
- MKVToolNix (mkvmerge, mkvextract)
- Requests library

### 🐛 Corrigido

- Problemas de CORS ao carregar ficheiros localmente
- Erro de parsing de multipart form data em Python 3.13
- Detecção incorreta de idioma em algumas tracks
- Cache de JavaScript impedindo atualizações

### 🚀 Performance

- Tradução de 1000 legendas: ~15 minutos
- Tradução de 1500 legendas: ~20-25 minutos
- Extração de legendas MKV: ~5 segundos
- Detecção de framerate: < 1 segundo

### 📚 Documentação

- README.md completo com exemplos
- Instruções de instalação
- Workflow completo de uso
- Exemplos reais de utilização
- Roadmap para v2.0

### 🎯 Resultados

- ✅ Timeframes: 100% corretos
- ✅ Traduções: 100% completas
- ✅ Quebras de linha: 99.3% corretas (após correção)
- ✅ Framerate: Detecção automática
- ✅ Idioma: Auto-detectado (60+ idiomas)

---

## [Unreleased] - v3.0 (Planejado)

### 🎯 Planejado

#### Conversão de Framerate
- Conversão automática entre framerates
- Ajuste de timestamps para sincronização
- Suporte para conversões personalizadas

#### Editor de Legendas
- Editor inline de legendas na interface web
- Edição de timestamps
- Pré-visualização em tempo real
- Desfazer/refazer

#### Formatos Adicionais
- Suporte para ASS/SSA
- Suporte para WebVTT
- Conversão entre formatos

#### Batch Processing
- Tradução de múltiplos ficheiros
- Processamento em paralelo
- Fila de trabalhos

#### Gestão
- Histórico de traduções
- Gestão segura de API keys
- Estatísticas de uso detalhadas
- Exportação de relatórios

#### Interface
- Temas personalizáveis
- Modo claro/escuro
- Atalhos de teclado
- Drag & drop melhorado

---

**Legendas:**
- `✨ Adicionado` - Nova funcionalidade
- `🔧 Melhorado` - Melhoria em funcionalidade existente
- `🐛 Corrigido` - Correção de bug
- `🚀 Performance` - Melhorias de performance
- `📚 Documentação` - Mudanças em documentação
- `🎯 Planejado` - Funcionalidades planejadas

[2.0.0]: https://github.com/username/scriptum/releases/tag/v2.0.0
[1.0.0]: https://github.com/username/scriptum/releases/tag/v1.0.0
