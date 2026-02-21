"""
Movie recognition service
Handles TMDB API integration for movie metadata
"""
import requests
from typing import Dict, Any, Optional
from pathlib import Path
import re


class MovieService:
    """Service for movie recognition and metadata"""

    def __init__(self, api_key: str):
        """
        Initialize movie service

        Args:
            api_key: TMDB API key
        """
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w300"

    def parse_filename(self, filename: str) -> Dict[str, Optional[str]]:
        """
        Extract title, year, and TV show info from filename.
        Handles both movies and TV shows (S01E01 pattern).
        """
        name = Path(filename).stem

        # Detect TV show: S01E01, s01e01, 1x01, etc.
        tv_match = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})', name)
        is_tv = bool(tv_match)

        # Extract title: everything before S01E01 or quality tags
        # Quality tags: 1080p, 720p, BluRay, WEBRip, HEVC, x264, x265, HDRip, etc.
        quality_pattern = r'[\.\s]+((?:\d{3,4}[pi]|[Bb]lu[Rr]ay|WEB(?:Rip|DL|-DL)?|HDTV|HEVC|[Xx]26[45]|H\.?26[45]|AAC|AC3|DTS|HDR|DoVi|REMUX|PROPER|REPACK|PSA|YTS|YIFY|NF|AMZN|DSNP).*)$'

        # For TV shows, title is before the SxxExx
        if tv_match:
            title_part = name[:tv_match.start()]
        else:
            # Try to cut at quality tags
            quality_match = re.search(quality_pattern, name, re.IGNORECASE)
            title_part = name[:quality_match.start()] if quality_match else name

        # Extract year: 4-digit number between 1920-2035, NOT followed by 'p' (resolution)
        year = None
        year_match = re.search(r'(?<!\d)(19[2-9]\d|20[0-3]\d)(?!\d)(?!p)', title_part or name, re.IGNORECASE)
        if year_match:
            year = year_match.group(1)
            # Remove year from title
            title_part = title_part[:year_match.start()] + title_part[year_match.end():]

        title = title_part.replace('.', ' ').replace('_', ' ').strip()
        # Clean trailing separators
        title = re.sub(r'[\s\-_]+$', '', title)

        return {
            'title': title,
            'year': year,
            'is_tv': is_tv,
            'season': tv_match.group(1) if tv_match else None,
            'episode': tv_match.group(2) if tv_match else None,
        }

    def search_tv(self, title: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Search TMDB for a TV show."""
        if not self.api_key:
            return None
        try:
            params = {'api_key': self.api_key, 'query': title, 'language': 'pt-BR'}
            if year:
                params['first_air_date_year'] = year
            response = requests.get(f"{self.base_url}/search/tv", params=params, timeout=10)
            if response.status_code != 200:
                return None
            results = response.json().get('results', [])
            if not results:
                return None
            show = results[0]
            return {
                'id': show.get('id'),
                'title': show.get('name', ''),
                'original_title': show.get('original_name', ''),
                'year': show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                'rating': round(show.get('vote_average', 0), 1),
                'poster': f"{self.image_base_url}{show.get('poster_path')}" if show.get('poster_path') else '',
                'overview': show.get('overview', ''),
                'imdb_id': None,
                'media_type': 'tv',
            }
        except Exception as e:
            print(f"❌ Error searching TV show: {e}")
            return None

    def search_movie(self, title: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for movie by title and optional year

        Args:
            title: Movie title
            year: Release year (optional)

        Returns:
            Movie metadata dictionary or None if not found
        """
        if not self.api_key:
            print("⚠️  TMDB API key not configured")
            return None

        try:
            params = {
                'api_key': self.api_key,
                'query': title,
                'language': 'pt-BR'
            }

            if year:
                params['year'] = year

            response = requests.get(
                f"{self.base_url}/search/movie",
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️  TMDB search failed: {response.status_code}")
                return None

            data = response.json()
            results = data.get('results', [])

            if not results:
                return None

            # Return first result
            movie = results[0]

            return {
                'id': movie.get('id'),
                'title': movie.get('title', ''),
                'original_title': movie.get('original_title', ''),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                'rating': round(movie.get('vote_average', 0), 1),
                'poster': f"{self.image_base_url}{movie.get('poster_path')}" if movie.get('poster_path') else '',
                'overview': movie.get('overview', ''),
                'imdb_id': None,
                'media_type': 'movie',
            }

        except Exception as e:
            print(f"❌ Error searching movie: {e}")
            return None

    def get_movie_by_imdb_id(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Get movie by IMDB ID

        Args:
            imdb_id: IMDB ID (e.g., tt1234567)

        Returns:
            Movie metadata dictionary or None if not found
        """
        if not self.api_key:
            print("⚠️  TMDB API key not configured")
            return None

        try:
            response = requests.get(
                f"{self.base_url}/find/{imdb_id}",
                params={
                    'api_key': self.api_key,
                    'external_source': 'imdb_id',
                    'language': 'pt-BR'
                },
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️  TMDB find failed: {response.status_code}")
                return None

            data = response.json()
            results = data.get('movie_results', [])

            if not results:
                return None

            movie = results[0]

            return {
                'id': movie.get('id'),
                'title': movie.get('title', ''),
                'original_title': movie.get('original_title', ''),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                'rating': round(movie.get('vote_average', 0), 1),
                'poster': f"{self.image_base_url}{movie.get('poster_path')}" if movie.get('poster_path') else '',
                'overview': movie.get('overview', ''),
                'imdb_id': imdb_id
            }

        except Exception as e:
            print(f"❌ Error fetching movie by IMDB ID: {e}")
            return None

    def recognize_from_filename(self, filename: str, imdb_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Recognize movie from filename with optional IMDB ID fallback

        Args:
            filename: Video filename
            imdb_id: Optional IMDB ID for direct lookup

        Returns:
            Movie metadata dictionary or None if not found
        """
        print(f"🎬 Recognizing movie from: {filename}")

        # Try IMDB ID first if provided
        if imdb_id:
            print(f"🔍 Searching by IMDB ID: {imdb_id}")
            movie = self.get_movie_by_imdb_id(imdb_id)
            if movie:
                print(f"✅ Found: {movie['title']} ({movie['year']})")
                return movie

        # Parse filename
        parsed = self.parse_filename(filename)
        is_tv = parsed.get('is_tv', False)
        print(f"📝 Parsed: '{parsed['title']}'" +
              (f" S{parsed['season']}E{parsed['episode']}" if is_tv else "") +
              (f" ({parsed['year']})" if parsed['year'] else "") +
              (" [TV]" if is_tv else " [Movie]"))

        result = None

        if is_tv:
            # TV show: search TV first, fall back to movie
            result = self.search_tv(parsed['title'], parsed['year'])
            if not result:
                print("⚠️  TV search failed, trying movie search...")
                result = self.search_movie(parsed['title'], parsed['year'])
        else:
            # Movie: search movie first, fall back to TV
            result = self.search_movie(parsed['title'], parsed['year'])
            if not result:
                print("⚠️  Movie search failed, trying TV search...")
                result = self.search_tv(parsed['title'], parsed['year'])

        if result:
            print(f"✅ Found: {result['title']} ({result['year']}) [{result.get('media_type', 'unknown')}]")
        else:
            print("❌ Not found")

        return result
