#!/usr/bin/env python3
"""
Movie Detector - Extrai informações de filme a partir do nome do ficheiro
"""

import re
from typing import Optional, Dict, Tuple


class MovieDetector:
    """Detecta informações de filmes a partir de nomes de ficheiros"""

    # Padrões comuns de nomes de ficheiros
    PATTERNS = [
        # Nome.Ano.qualidade.srt
        r'(.+?)[.\s]+(\d{4})[.\s]+',
        # Nome (Ano) qualidade.srt
        r'(.+?)\s*\((\d{4})\)',
        # Nome.S01E01.srt (séries)
        r'(.+?)[.\s]+[Ss](\d{2})[Ee](\d{2})',
        # Nome - qualidade.srt
        r'(.+?)\s*[-]\s*',
        # Nome apenas
        r'(.+?)(?:\.[a-z]{2,3})?$'
    ]

    QUALITY_MARKERS = [
        '1080p', '720p', '480p', '4k', '2160p',
        'bluray', 'brrip', 'webrip', 'web-dl', 'hdtv',
        'dvdrip', 'xvid', 'x264', 'x265', 'hevc'
    ]

    LANGUAGE_CODES = ['en', 'pt', 'es', 'fr', 'de', 'it', 'pt-pt', 'pt-br']

    def __init__(self):
        pass

    def detect_from_filename(self, filename: str) -> Dict:
        """
        Detecta informações do filme a partir do nome do ficheiro

        Args:
            filename: Nome do ficheiro (ex: "Inception.2010.1080p.en.srt")

        Returns:
            Dict com: title, year, season, episode, language
        """
        # Remover extensão
        basename = filename
        if '.' in filename:
            basename = '.'.join(filename.split('.')[:-1])

        # Limpar caracteres especiais
        basename = basename.replace('_', ' ')

        result = {
            'title': None,
            'year': None,
            'season': None,
            'episode': None,
            'language': None,
            'original_filename': filename,
            'is_series': False
        }

        # Detectar idioma (só se for palavra separada)
        for lang in self.LANGUAGE_CODES:
            # Procurar o código de idioma como palavra separada (com pontos ou hífens)
            pattern = r'[.\-_]' + re.escape(lang.lower()) + r'[.\-_]'
            if re.search(pattern, basename.lower()):
                result['language'] = lang
                # Remover o código de idioma
                basename = re.sub(pattern, '.', basename, flags=re.IGNORECASE)

        # Remover marcadores de qualidade
        cleaned = basename
        for marker in self.QUALITY_MARKERS:
            cleaned = re.sub(marker, '', cleaned, flags=re.IGNORECASE)

        # Tentar detectar série (S01E01)
        series_match = re.search(r'[Ss](\d{2})[Ee](\d{2})', basename)
        if series_match:
            result['is_series'] = True
            result['season'] = int(series_match.group(1))
            result['episode'] = int(series_match.group(2))
            # Extrair título antes do SxxExx
            title_match = re.match(r'(.+?)[.\s]+[Ss]\d{2}[Ee]\d{2}', basename)
            if title_match:
                result['title'] = self._clean_title(title_match.group(1))

        # Tentar detectar ano
        year_match = re.search(r'[.\s\(](\d{4})[.\s\)]', basename)
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2030:
                result['year'] = year
                # Extrair título antes do ano
                title_match = re.match(r'(.+?)[.\s]+\(?\d{4}\)?', basename)
                if title_match:
                    result['title'] = self._clean_title(title_match.group(1))

        # Se ainda não temos título, usar todo o nome limpo
        if not result['title']:
            result['title'] = self._clean_title(cleaned)

        return result

    def _clean_title(self, title: str) -> str:
        """Limpa e formata o título do filme"""
        # Remover pontos e underscores
        title = title.replace('.', ' ').replace('_', ' ')

        # Remover múltiplos espaços
        title = re.sub(r'\s+', ' ', title)

        # Remover espaços nas extremidades
        title = title.strip()

        # Remover marcadores de qualidade residuais
        for marker in self.QUALITY_MARKERS:
            title = re.sub(marker, '', title, flags=re.IGNORECASE)

        # Capitalizar palavras (Title Case)
        title = title.title()

        return title.strip()

    def format_search_query(self, movie_info: Dict) -> str:
        """
        Formata query de pesquisa para APIs

        Args:
            movie_info: Dicionário retornado por detect_from_filename

        Returns:
            String formatada para pesquisa
        """
        query = movie_info['title']

        if movie_info['year']:
            query += f" {movie_info['year']}"

        return query

    def parse_filename_batch(self, filenames: list) -> list:
        """
        Processa múltiplos ficheiros de uma vez

        Args:
            filenames: Lista de nomes de ficheiros

        Returns:
            Lista de dicionários com informações
        """
        return [self.detect_from_filename(f) for f in filenames]


def main():
    """Testes do detector"""
    detector = MovieDetector()

    test_files = [
        "Inception.2010.1080p.BluRay.en.srt",
        "The Matrix (1999) 720p.srt",
        "Breaking.Bad.S01E01.720p.srt",
        "Zootopia.2016.pt-pt.srt",
        "Interstellar 2014.srt",
        "Game.of.Thrones.S08E06.1080p.WEB-DL.srt",
        "Orwell_en.srt"
    ]

    print("🎬 Movie Detector - Testes\n")

    for filename in test_files:
        info = detector.detect_from_filename(filename)
        print(f"📄 {filename}")
        print(f"   Título: {info['title']}")
        if info['year']:
            print(f"   Ano: {info['year']}")
        if info['is_series']:
            print(f"   Série: S{info['season']:02d}E{info['episode']:02d}")
        if info['language']:
            print(f"   Idioma: {info['language']}")
        print(f"   Query: {detector.format_search_query(info)}")
        print()


if __name__ == '__main__':
    main()
