#!/usr/bin/env python3
"""
TMDB Fetcher - Busca metadados de filmes/séries na API do TMDB
"""

import os
import requests
import json
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

# Carregar .env manualmente
def load_env():
    """Carrega variáveis do ficheiro .env"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()


class TMDBFetcher:
    """Fetcher de metadados do The Movie Database (TMDB)"""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o fetcher

        Args:
            api_key: Chave da API TMDB (pode ser None para modo demo)
        """
        self.api_key = api_key or os.environ.get('TMDB_API_KEY')
        self.session = requests.Session()

        if self.api_key:
            print(f"🔑 TMDB Fetcher inicializado com API key")
        else:
            print(f"⚠️  TMDB Fetcher em modo mock (sem API key)")

    def search_movie(self, title: str, year: Optional[int] = None) -> List[Dict]:
        """
        Pesquisa filme por título

        Args:
            title: Título do filme
            year: Ano opcional para filtrar

        Returns:
            Lista de resultados
        """
        if not self.api_key:
            raise ValueError("TMDB API key não configurada! Defina TMDB_API_KEY no ficheiro .env")

        params = {
            'api_key': self.api_key,
            'query': title,
            'language': 'pt-PT'
        }

        if year:
            params['year'] = year

        try:
            response = self.session.get(
                f"{self.BASE_URL}/search/movie",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"❌ Erro ao buscar no TMDB: {e}")
            raise

    def get_movie_details(self, movie_id: int) -> Dict:
        """
        Obtém detalhes completos do filme

        Args:
            movie_id: ID do filme no TMDB

        Returns:
            Dicionário com detalhes completos
        """
        if not self.api_key:
            return {}

        params = {
            'api_key': self.api_key,
            'language': 'pt-PT',
            'append_to_response': 'credits,keywords'
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/{movie_id}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Erro ao buscar detalhes: {e}")
            return {}

    def get_credits(self, movie_id: int) -> Dict:
        """
        Obtém elenco e equipe do filme

        Args:
            movie_id: ID do filme no TMDB

        Returns:
            Dicionário com cast e crew
        """
        if not self.api_key:
            return {'cast': [], 'crew': []}

        params = {
            'api_key': self.api_key,
            'language': 'pt-PT'
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/movie/{movie_id}/credits",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Erro ao buscar créditos: {e}")
            return {'cast': [], 'crew': []}

    def get_movie_metadata(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Busca e compila todos os metadados de um filme

        Args:
            title: Título do filme
            year: Ano opcional

        Returns:
            Dicionário completo com metadados ou None
        """
        # Buscar filme
        results = self.search_movie(title, year)

        if not results:
            print(f"❌ Filme não encontrado: {title}")
            return None

        # Pegar primeiro resultado (mais relevante)
        movie = results[0]
        movie_id = movie['id']

        # Buscar detalhes completos
        details = self.get_movie_details(movie_id) if self.api_key else movie
        credits = self.get_credits(movie_id) if self.api_key else {'cast': [], 'crew': []}

        # Compilar metadados
        metadata = {
            'id': movie_id,
            'title': movie.get('title', title),
            'original_title': movie.get('original_title'),
            'year': self._extract_year(movie.get('release_date', '')),
            'overview': movie.get('overview', ''),
            'genres': [g['name'] for g in details.get('genres', [])] if self.api_key else [],
            'rating': movie.get('vote_average', 0),
            'poster_path': self._get_full_image_url(movie.get('poster_path')),
            'backdrop_path': self._get_full_image_url(movie.get('backdrop_path')),
            'runtime': details.get('runtime'),
            'tagline': details.get('tagline', ''),

            # Elenco principal (top 10)
            'cast': [
                {
                    'name': person['name'],
                    'character': person['character'],
                    'order': person.get('order', 999)
                }
                for person in credits.get('cast', [])[:10]
            ],

            # Diretor
            'director': next(
                (person['name'] for person in credits.get('crew', [])
                 if person['job'] == 'Director'),
                None
            )
        }

        return metadata

    def create_character_glossary(self, metadata: Dict) -> Dict[str, str]:
        """
        Cria glossário de personagens para preservar nomes

        Args:
            metadata: Metadados do filme

        Returns:
            Dicionário nome_personagem -> nome_personagem (não traduzir)
        """
        glossary = {}

        if not metadata or 'cast' not in metadata:
            return glossary

        for person in metadata['cast']:
            character = person['character']

            # Extrair primeiro nome do personagem
            # Ex: "Cobb" de "Dom Cobb"
            if character:
                # Remover texto entre parênteses
                character = character.split('(')[0].strip()

                # Pegar palavras
                words = character.split()

                # Adicionar todos os nomes ao glossário
                for word in words:
                    if len(word) > 1:  # Ignorar iniciais
                        glossary[word] = word

        return glossary

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extrai ano de string de data"""
        if not date_str:
            return None
        try:
            return int(date_str[:4])
        except:
            return None

    def _get_full_image_url(self, path: Optional[str]) -> Optional[str]:
        """Converte path relativo em URL completa"""
        if not path:
            return None
        return f"{self.IMAGE_BASE}{path}"


def main():
    """Testes do fetcher"""
    print("🎬 TMDB Fetcher - Testes (Mock Mode)\n")

    fetcher = TMDBFetcher()  # Sem API key = modo mock

    test_movies = [
        ('Inception', 2010),
        ('Zootopia', 2016),
        ('The Matrix', 1999),
    ]

    for title, year in test_movies:
        print(f"🔍 Buscando: {title} ({year})")
        metadata = fetcher.get_movie_metadata(title, year)

        if metadata:
            print(f"   ✅ {metadata['title']}")
            print(f"   ⭐ Rating: {metadata['rating']}/10")
            print(f"   🎭 Géneros: {', '.join(metadata['genres'])}")
            if metadata['cast']:
                print(f"   👥 Elenco: {len(metadata['cast'])} personagens")

            # Glossário
            glossary = fetcher.create_character_glossary(metadata)
            if glossary:
                print(f"   📝 Glossário: {len(glossary)} termos")
                print(f"      {list(glossary.keys())[:5]}")
        print()


if __name__ == '__main__':
    main()
