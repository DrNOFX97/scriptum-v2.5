#!/usr/bin/env python3
"""
OpenSubtitles API Integration
Busca e download de legendas do OpenSubtitles.com
"""

import requests
import os
import gzip
import base64
from pathlib import Path
import hashlib


class OpenSubtitlesAPI:
    """Cliente para API do OpenSubtitles"""

    BASE_URL = "https://api.opensubtitles.com/api/v1"

    def __init__(self, api_key=None):
        """
        Inicializa cliente OpenSubtitles

        Args:
            api_key: Chave API do OpenSubtitles (gratuita em opensubtitles.com)
        """
        self.api_key = api_key or os.getenv('OPENSUBTITLES_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenSubtitles API key não encontrada. "
                "Defina OPENSUBTITLES_API_KEY ou passe api_key no construtor. "
                "Obtenha uma chave gratuita em: https://www.opensubtitles.com/api"
            )

        self.headers = {
            'Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Scriptum v2.0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def calculate_movie_hash(self, video_path):
        """
        Calcula hash OpenSubtitles de um ficheiro de vídeo

        Args:
            video_path: Caminho para o ficheiro de vídeo

        Returns:
            str: Hash do ficheiro (16 caracteres hex)
        """
        longlongformat = 'Q'  # unsigned long long
        bytesize = 8
        fmt = f"<{bytesize}{longlongformat}"

        video_path = Path(video_path)
        filesize = video_path.stat().st_size

        if filesize < 65536 * 2:
            raise ValueError("Ficheiro muito pequeno para calcular hash")

        hash_value = filesize

        # Read first and last 64KB
        with open(video_path, 'rb') as f:
            # First 64KB
            for _ in range(65536 // bytesize):
                buffer = f.read(bytesize)
                (value,) = struct.unpack(fmt, buffer)
                hash_value += value
                hash_value &= 0xFFFFFFFFFFFFFFFF

            # Last 64KB
            f.seek(max(0, filesize - 65536), 0)
            for _ in range(65536 // bytesize):
                buffer = f.read(bytesize)
                (value,) = struct.unpack(fmt, buffer)
                hash_value += value
                hash_value &= 0xFFFFFFFFFFFFFFFF

        return f"{hash_value:016x}"

    def search_by_hash(self, video_path, languages=['pt', 'en']):
        """
        Busca legendas por hash do ficheiro (mais preciso)

        Args:
            video_path: Caminho para o ficheiro de vídeo
            languages: Lista de idiomas (códigos ISO 639-1)

        Returns:
            list: Lista de legendas encontradas
        """
        try:
            movie_hash = self.calculate_movie_hash(video_path)
            filesize = Path(video_path).stat().st_size

            params = {
                'moviehash': movie_hash,
                'languages': ','.join(languages)
            }

            response = self.session.get(f"{self.BASE_URL}/subtitles", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except Exception as e:
            print(f"Erro ao buscar por hash: {e}")
            return []

    def search_by_query(self, query, year=None, languages=['pt', 'en'], season=None, episode=None):
        """
        Busca legendas por nome do filme/série

        Args:
            query: Nome do filme ou série
            year: Ano (opcional)
            languages: Lista de idiomas
            season: Temporada (para séries)
            episode: Episódio (para séries)

        Returns:
            list: Lista de legendas encontradas
        """
        params = {
            'query': query,
            'languages': ','.join(languages)
        }

        if year:
            params['year'] = year
        if season:
            params['season_number'] = season
        if episode:
            params['episode_number'] = episode

        try:
            response = self.session.get(f"{self.BASE_URL}/subtitles", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except Exception as e:
            print(f"Erro ao buscar por query: {e}")
            return []

    def search_by_imdb_id(self, imdb_id, languages=['pt', 'en']):
        """
        Busca legendas por IMDB ID

        Args:
            imdb_id: ID do IMDB (ex: "tt0133093")
            languages: Lista de idiomas

        Returns:
            list: Lista de legendas encontradas
        """
        params = {
            'imdb_id': imdb_id.replace('tt', ''),  # Remove 'tt' prefix
            'languages': ','.join(languages)
        }

        try:
            response = self.session.get(f"{self.BASE_URL}/subtitles", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except Exception as e:
            print(f"Erro ao buscar por IMDB ID: {e}")
            return []

    def download_subtitle(self, file_id, output_path=None):
        """
        Download de legenda

        Args:
            file_id: ID do ficheiro de legenda
            output_path: Caminho para salvar (opcional)

        Returns:
            str: Caminho do ficheiro descarregado
        """
        # Request download link
        payload = {'file_id': file_id}
        response = self.session.post(f"{self.BASE_URL}/download", json=payload)
        response.raise_for_status()

        data = response.json()
        download_url = data.get('link')

        if not download_url:
            raise Exception("URL de download não disponível")

        # Download subtitle file
        sub_response = requests.get(download_url)
        sub_response.raise_for_status()

        # Save file
        if not output_path:
            output_path = f"subtitle_{file_id}.srt"

        output_path = Path(output_path)
        output_path.write_bytes(sub_response.content)

        print(f"✅ Legenda descarregada: {output_path}")
        return str(output_path)

    def get_best_subtitle(self, subtitles, prefer_language='pt'):
        """
        Seleciona a melhor legenda da lista

        Args:
            subtitles: Lista de legendas
            prefer_language: Idioma preferido

        Returns:
            dict: Melhor legenda encontrada
        """
        if not subtitles:
            return None

        # Filter by preferred language
        lang_subs = [s for s in subtitles if s['attributes']['language'] == prefer_language]

        # If no subtitles in preferred language, use all
        if not lang_subs:
            lang_subs = subtitles

        # Sort by downloads and ratings
        def score(sub):
            attrs = sub['attributes']
            downloads = attrs.get('download_count', 0)
            ratings = attrs.get('ratings', 0)
            votes = attrs.get('votes', 0)
            return downloads * 0.5 + ratings * votes * 0.5

        lang_subs.sort(key=score, reverse=True)
        return lang_subs[0]

    def format_subtitle_info(self, subtitle):
        """
        Formata informações da legenda para exibição

        Args:
            subtitle: Dados da legenda

        Returns:
            dict: Informações formatadas
        """
        attrs = subtitle['attributes']
        files = attrs.get('files', [{}])[0]

        return {
            'id': files.get('file_id'),
            'language': attrs.get('language'),
            'release': attrs.get('release', 'N/A'),
            'uploader': attrs.get('uploader', {}).get('name', 'Unknown'),
            'downloads': attrs.get('download_count', 0),
            'rating': attrs.get('ratings', 0),
            'votes': attrs.get('votes', 0),
            'hearing_impaired': attrs.get('hearing_impaired', False),
            'fps': attrs.get('fps', 0),
            'url': attrs.get('url', '')
        }


# Adicionar import necessário
import struct


def search_and_download(video_path=None, query=None, imdb_id=None, output_path=None, language='pt'):
    """
    Função de conveniência para buscar e descarregar legenda

    Args:
        video_path: Caminho do vídeo (para busca por hash)
        query: Nome do filme (busca por texto)
        imdb_id: IMDB ID (busca por ID)
        output_path: Onde salvar a legenda
        language: Idioma preferido

    Returns:
        str: Caminho da legenda descarregada
    """
    api = OpenSubtitlesAPI()

    print("🔍 A procurar legendas...")

    # Try different search methods
    subtitles = []

    if video_path and Path(video_path).exists():
        print(f"   Buscando por hash do ficheiro...")
        subtitles = api.search_by_hash(video_path, languages=[language, 'en'])

    if not subtitles and imdb_id:
        print(f"   Buscando por IMDB ID: {imdb_id}...")
        subtitles = api.search_by_imdb_id(imdb_id, languages=[language, 'en'])

    if not subtitles and query:
        print(f"   Buscando por nome: {query}...")
        subtitles = api.search_by_query(query, languages=[language, 'en'])

    if not subtitles:
        print("❌ Nenhuma legenda encontrada")
        return None

    print(f"✅ {len(subtitles)} legendas encontradas")

    # Get best subtitle
    best = api.get_best_subtitle(subtitles, prefer_language=language)
    info = api.format_subtitle_info(best)

    print(f"\n📄 Melhor legenda:")
    print(f"   Idioma:     {info['language']}")
    print(f"   Release:    {info['release']}")
    print(f"   Downloads:  {info['downloads']}")
    print(f"   Rating:     {info['rating']}/10 ({info['votes']} votos)")
    print(f"   FPS:        {info['fps']}")

    # Download
    print(f"\n💾 A descarregar...")
    downloaded = api.download_subtitle(info['id'], output_path)

    return downloaded


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("=" * 70)
        print("🎬 OpenSubtitles Downloader")
        print("=" * 70)
        print("\nUso:")
        print("  python3 opensubtitles_api.py <video_file>")
        print("  python3 opensubtitles_api.py --query \"Movie Name\" [--year 2020]")
        print("  python3 opensubtitles_api.py --imdb tt0133093")
        print("\nExemplos:")
        print('  python3 opensubtitles_api.py "movie.mkv"')
        print('  python3 opensubtitles_api.py --query "The Matrix" --year 1999')
        print('  python3 opensubtitles_api.py --imdb tt0133093')
        print("\nNota: Configure OPENSUBTITLES_API_KEY como variável de ambiente")
        print("      Obtenha chave gratuita em: https://www.opensubtitles.com/api")
        print("=" * 70)
        sys.exit(1)

    # Parse arguments
    if '--query' in sys.argv:
        idx = sys.argv.index('--query')
        query = sys.argv[idx + 1]
        year = None
        if '--year' in sys.argv:
            year_idx = sys.argv.index('--year')
            year = int(sys.argv[year_idx + 1])
        search_and_download(query=query, language='pt')

    elif '--imdb' in sys.argv:
        idx = sys.argv.index('--imdb')
        imdb_id = sys.argv[idx + 1]
        search_and_download(imdb_id=imdb_id, language='pt')

    else:
        video_file = sys.argv[1]
        if not Path(video_file).exists():
            print(f"❌ Ficheiro não encontrado: {video_file}")
            sys.exit(1)
        search_and_download(video_path=video_file, language='pt')
