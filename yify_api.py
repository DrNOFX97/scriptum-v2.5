#!/usr/bin/env python3
"""
YIFY Subtitles API - Alternativa gratuita sem necessidade de API key
"""

import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
import zipfile
import io


class YifyAPI:
    """Cliente para YifySubtitles.org (sem necessidade de API key)"""

    BASE_URL = "https://yifysubtitles.ch"  # Changed from .org to .ch

    def __init__(self, timeout=10):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        })
        self.timeout = timeout

    def search(self, query):
        """
        Busca filme por nome

        Args:
            query: Nome do filme

        Returns:
            list: Lista de filmes encontrados
        """
        search_url = f"{self.BASE_URL}/search"

        try:
            response = self.session.get(search_url, params={'q': query}, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            results = []

            # Parse search results - try multiple selectors
            for item in soup.select('.media.movie-container, .movie-item, .result-item'):
                title_elem = item.select_one('.media-heading a, .title a, h3 a')
                if title_elem:
                    year_elem = item.select_one('.movinfo span, .year, .date')
                    year = year_elem.text.strip() if year_elem else 'N/A'

                    # Clean URL
                    href = title_elem.get('href', '')
                    if href.startswith('/'):
                        href = self.BASE_URL + href
                    elif not href.startswith('http'):
                        continue

                    results.append({
                        'title': title_elem.text.strip(),
                        'url': href,
                        'year': year
                    })

            if not results:
                print("⚠️  Nenhum resultado encontrado ou mudança no HTML do site")

            return results

        except requests.Timeout:
            print(f"❌ Timeout ao buscar no YIFY (>{self.timeout}s)")
            return []
        except requests.RequestException as e:
            print(f"❌ Erro na conexão com YIFY: {e}")
            return []
        except Exception as e:
            print(f"❌ Erro ao processar resposta YIFY: {e}")
            return []

    def get_subtitles(self, movie_url, language='Portuguese'):
        """
        Obtém lista de legendas para um filme

        Args:
            movie_url: URL do filme
            language: Idioma (Portuguese, English, etc.)

        Returns:
            list: Lista de legendas disponíveis
        """
        try:
            response = self.session.get(movie_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            subtitles = []

            # Find subtitle rows
            for row in soup.select('tbody tr, .subtitle-row, .subtitle-entry'):
                # Check language
                lang_elem = row.select_one('.flag-cell .sub-lang, .language, .lang')
                if not lang_elem:
                    continue

                sub_lang = lang_elem.text.strip()

                # Match language (support Brazilian Portuguese and Portuguese)
                if sub_lang == language or \
                   (language == 'Portuguese' and 'Brazilian' in sub_lang) or \
                   (language == 'Portuguese' and 'Português' in sub_lang):

                    # Get subtitle info
                    rating_elem = row.select_one('.rating-cell span, .rating')
                    rating = 0
                    if rating_elem:
                        try:
                            rating = int(rating_elem.text.strip())
                        except:
                            rating = 0

                    uploader_elem = row.select_one('.uploader-cell a, .uploader')
                    uploader = uploader_elem.text.strip() if uploader_elem else 'Anonymous'

                    download_elem = row.select_one('.download-cell a, .download-link a')
                    if download_elem:
                        href = download_elem.get('href', '')
                        if not href:
                            continue

                        subtitle_id = href.split('/')[-1]

                        # Build subtitle URL
                        if href.startswith('/'):
                            sub_url = self.BASE_URL + href
                        elif href.startswith('http'):
                            sub_url = href
                        else:
                            continue

                        subtitles.append({
                            'id': subtitle_id,
                            'language': sub_lang,
                            'rating': rating,
                            'uploader': uploader,
                            'url': sub_url
                        })

            if not subtitles:
                print(f"⚠️  Nenhuma legenda em {language} encontrada ou mudança no HTML")

            return subtitles

        except requests.Timeout:
            print(f"❌ Timeout ao obter legendas (>{self.timeout}s)")
            return []
        except requests.RequestException as e:
            print(f"❌ Erro na conexão: {e}")
            return []
        except Exception as e:
            print(f"❌ Erro ao processar legendas: {e}")
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
            response = self.session.get(subtitle_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find download button - try multiple selectors
            download_btn = soup.select_one('.download-subtitle, .btn-download, a.download-btn, a[href*="download"]')
            if not download_btn:
                raise Exception("Botão de download não encontrado no HTML")

            href = download_btn.get('href', '')
            if href.startswith('/'):
                download_url = self.BASE_URL + href
            elif href.startswith('http'):
                download_url = href
            else:
                raise Exception(f"URL de download inválida: {href}")

            # Download file
            print(f"   💾 A descarregar de: {download_url}")
            download_response = self.session.get(download_url, timeout=self.timeout)
            download_response.raise_for_status()

            # It's always a zip file
            try:
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

                print(f"✅ Legenda descarregada: {output_path}")
                return str(output_path)

            except zipfile.BadZipFile:
                raise Exception("Ficheiro descarregado não é um ZIP válido")

        except requests.Timeout:
            print(f"❌ Timeout no download (>{self.timeout}s)")
            raise
        except requests.RequestException as e:
            print(f"❌ Erro na conexão durante download: {e}")
            raise
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            raise


def search_and_download(query, language='Portuguese', output_path=None):
    """
    Busca e descarrega legenda

    Args:
        query: Nome do filme
        language: Idioma preferido
        output_path: Onde salvar

    Returns:
        str: Caminho da legenda descarregada
    """
    api = YifyAPI()

    print(f"🔍 Procurando '{query}' no YIFY Subtitles...")

    # Search for movie
    results = api.search(query)

    if not results:
        print("❌ Nenhum resultado encontrado")
        return None

    print(f"\n✅ {len(results)} resultados encontrados:")
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result['title']} ({result['year']})")

    # Use first result
    movie = results[0]
    print(f"\n📄 Buscando legendas para: {movie['title']}")

    # Get subtitles
    subtitles = api.get_subtitles(movie['url'], language=language)

    if not subtitles:
        print(f"❌ Nenhuma legenda em {language} encontrada")
        return None

    print(f"\n✅ {len(subtitles)} legendas encontradas:")

    # Sort by rating
    subtitles.sort(key=lambda x: x['rating'], reverse=True)

    for i, sub in enumerate(subtitles[:5], 1):
        print(f"   {i}. Rating: {sub['rating']}/5 - Uploader: {sub['uploader']}")

    # Download best rated subtitle
    print(f"\n💾 A descarregar melhor legenda (rating: {subtitles[0]['rating']}/5)...")
    downloaded = api.download_subtitle(subtitles[0]['url'], output_path)

    return downloaded


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("=" * 70)
        print("🎬 YIFY Subtitles Downloader")
        print("=" * 70)
        print("\nUso:")
        print("  python3 yify_api.py <movie_name> [language]")
        print("\nExemplos:")
        print('  python3 yify_api.py "The Matrix"')
        print('  python3 yify_api.py "Inception" English')
        print("\nIdiomas disponíveis:")
        print("  Portuguese, English, Spanish, French, etc.")
        print("\n✅ Não requer API key!")
        print("=" * 70)
        sys.exit(1)

    query = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'Portuguese'

    search_and_download(query, language=language)
