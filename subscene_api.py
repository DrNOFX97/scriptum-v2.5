#!/usr/bin/env python3
"""
Subscene Subtitle Downloader
Alternativa ao OpenSubtitles sem necessidade de API key
"""

import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
import zipfile
import io


class SubsceneAPI:
    """Cliente para Subscene.com (sem necessidade de API key)"""

    BASE_URL = "https://subscene.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def search(self, query):
        """
        Busca filme/série por nome

        Args:
            query: Nome do filme ou série

        Returns:
            list: Lista de resultados
        """
        search_url = f"{self.BASE_URL}/subtitles/searchbytitle"

        try:
            response = self.session.post(search_url, data={'query': query})
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            results = []

            # Parse search results
            for item in soup.select('.search-result'):
                title_elem = item.select_one('.title a')
                if title_elem:
                    results.append({
                        'title': title_elem.text.strip(),
                        'url': self.BASE_URL + title_elem['href'],
                        'type': 'movie' if '/movie/' in title_elem['href'] else 'series'
                    })

            return results

        except Exception as e:
            print(f"Erro na busca: {e}")
            return []

    def get_subtitles(self, movie_url, language='Portuguese'):
        """
        Obtém lista de legendas para um filme

        Args:
            movie_url: URL do filme no Subscene
            language: Idioma (Portuguese, English, etc.)

        Returns:
            list: Lista de legendas disponíveis
        """
        try:
            response = self.session.get(movie_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            subtitles = []

            # Find language section
            current_lang = None
            for row in soup.select('tbody tr'):
                # Check if this is a language header
                lang_elem = row.select_one('.l')
                if lang_elem:
                    current_lang = lang_elem.text.strip()
                    continue

                # If we're in the right language section
                if current_lang == language:
                    link_elem = row.select_one('td.a1 a')
                    if link_elem:
                        span_elems = link_elem.select('span')
                        release_name = span_elems[0].text.strip() if len(span_elems) > 0 else 'Unknown'

                        # Get download info
                        comment = row.select_one('.a6 .comment')

                        subtitles.append({
                            'release': release_name,
                            'url': self.BASE_URL + link_elem['href'],
                            'comment': comment.text.strip() if comment else '',
                            'language': current_lang
                        })

            return subtitles

        except Exception as e:
            print(f"Erro ao obter legendas: {e}")
            return []

    def download_subtitle(self, subtitle_url, output_path=None):
        """
        Download de legenda

        Args:
            subtitle_url: URL da página da legenda
            output_path: Caminho para salvar

        Returns:
            str: Caminho do ficheiro descarregado
        """
        try:
            # Get subtitle page
            response = self.session.get(subtitle_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find download link
            download_link = soup.select_one('#downloadButton')
            if not download_link:
                raise Exception("Link de download não encontrado")

            download_url = self.BASE_URL + download_link['href']

            # Download file
            download_response = self.session.get(download_url)
            download_response.raise_for_status()

            # Check if it's a zip file
            content_type = download_response.headers.get('content-type', '')

            if 'zip' in content_type or download_url.endswith('.zip'):
                # Extract first .srt from zip
                with zipfile.ZipFile(io.BytesIO(download_response.content)) as z:
                    srt_files = [f for f in z.namelist() if f.endswith('.srt')]
                    if not srt_files:
                        raise Exception("Nenhum ficheiro .srt encontrado no ZIP")

                    # Extract first srt
                    srt_content = z.read(srt_files[0])

                    if not output_path:
                        output_path = srt_files[0]

                    output_path = Path(output_path)
                    output_path.write_bytes(srt_content)

            else:
                # Direct SRT file
                if not output_path:
                    output_path = "subtitle.srt"

                output_path = Path(output_path)
                output_path.write_bytes(download_response.content)

            print(f"✅ Legenda descarregada: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"❌ Erro no download: {e}")
            raise


def search_and_download(query, language='Portuguese', output_path=None):
    """
    Busca e descarre ga legenda

    Args:
        query: Nome do filme
        language: Idioma preferido
        output_path: Onde salvar

    Returns:
        str: Caminho da legenda descarregada
    """
    api = SubsceneAPI()

    print(f"🔍 Procurando '{query}' no Subscene...")

    # Search for movie
    results = api.search(query)

    if not results:
        print("❌ Nenhum resultado encontrado")
        return None

    print(f"\n✅ {len(results)} resultados encontrados:")
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result['title']} ({result['type']})")

    # Use first result
    movie = results[0]
    print(f"\n📄 Buscando legendas para: {movie['title']}")

    # Get subtitles
    subtitles = api.get_subtitles(movie['url'], language=language)

    if not subtitles:
        print(f"❌ Nenhuma legenda em {language} encontrada")
        return None

    print(f"\n✅ {len(subtitles)} legendas encontradas:")
    for i, sub in enumerate(subtitles[:5], 1):
        print(f"   {i}. {sub['release']}")

    # Download first subtitle
    print(f"\n💾 A descarregar: {subtitles[0]['release']}...")
    downloaded = api.download_subtitle(subtitles[0]['url'], output_path)

    return downloaded


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("=" * 70)
        print("🎬 Subscene Subtitle Downloader")
        print("=" * 70)
        print("\nUso:")
        print("  python3 subscene_api.py <movie_name> [language]")
        print("\nExemplos:")
        print('  python3 subscene_api.py "The Matrix"')
        print('  python3 subscene_api.py "Inception" English')
        print("\nIdiomas disponíveis:")
        print("  Portuguese, English, Spanish, French, etc.")
        print("=" * 70)
        sys.exit(1)

    query = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'Portuguese'

    search_and_download(query, language=language)
