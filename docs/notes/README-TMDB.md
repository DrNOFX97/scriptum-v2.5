# 🎬 Scriptum - Integração TMDB

Sistema completo de metadados de filmes usando a API do TMDB.

## ✅ O Que Está Pronto

### Backend Python
- ✅ `metadata/movie_detector.py` - Detecção de filme do filename
- ✅ `metadata/tmdb_fetcher.py` - Busca de metadados do TMDB
- ✅ `metadata/movie_metadata_manager.py` - Sistema integrado
- ✅ `fetch_movie.py` - Script CLI para gerar JSON
- ✅ `.env` - API key configurada e segura

### Dados Disponíveis
- ✅ Título (em PT-PT!)
- ✅ Ano de lançamento
- ✅ Rating/Classificação
- ✅ Poster/Capa (URL completo)
- ✅ Géneros
- ✅ Sinopse (em PT-PT!)
- ✅ Elenco completo com personagens
- ✅ Glossário automático de nomes
- ✅ Contexto para tradução

## 🚀 Como Usar

### 1. Buscar Metadados via CLI

```bash
python3 fetch_movie.py "Inception.2010.en.srt"
```

Retorna JSON completo com todos os dados do filme.

### 2. Ver Exemplo Visual

Abre `show-movie.html` para ver exemplo com dados reais do filme Inception.

## 📋 Exemplo de Output

```json
{
  "metadata": {
    "title": "A Origem",
    "year": 2010,
    "rating": 8.37,
    "runtime": 148,
    "genres": ["Ação", "Ficção científica", "Aventura"],
    "overview": "Don Cobb é perito em roubar segredos...",
    "poster_path": "https://image.tmdb.org/t/p/w500/ms1bJvwa4BJycBakQ7afcedGlwY.jpg",
    "cast": [
      {"character": "Dom Cobb", "name": "Leonardo DiCaprio"},
      {"character": "Arthur", "name": "Joseph Gordon-Levitt"},
      ...
    ]
  },
  "glossary": {
    "Dom": "Dom",
    "Cobb": "Cobb",
    "Arthur": "Arthur",
    ...
  },
  "context": "Filme: A Origem (2010). Géneros: Ação, Ficção científica..."
}
```

## 🔑 API Key

A API key do TMDB está guardada em `.env`:
```
TMDB_API_KEY=71790f9d7c0f5b24e9bed93499f5cb96
```

**Nunca** fazer commit deste ficheiro!

## 🎯 Próximos Passos

1. ✅ Backend funcionando 100%
2. 🔄 Integrar com interface web
3. ⏳ Servidor HTTP (opcional)
4. ⏳ Cache de metadados

## 📝 Notas Importantes

- **Zero mock data** - Tudo vem do TMDB real
- **PT-PT** - Todos os textos em português de Portugal
- **Glossário** - Extrai automaticamente nomes de personagens
- **Contexto** - Gera resumo para melhorar tradução
- **Imagens** - URLs completos para posters em alta qualidade

---

**Última atualização:** 2026-01-29
**Status:** ✅ Funcional e testado
