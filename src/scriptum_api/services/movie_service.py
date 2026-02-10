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
        Extract movie name and year from filename

        Args:
            filename: Video filename

        Returns:
            Dictionary with 'title' and 'year' keys
        """
        # Remove file extension
        name = Path(filename).stem

        # Common patterns: Movie.Name.2024.1080p.BluRay
        patterns = [
            r'(.+?)[\.\s]+(\d{4})',  # Movie.Name.2024 or Movie Name 2024
            r'(.+?)[\(\[](\d{4})[\)\]]',  # Movie Name (2024) or [2024]
        ]

        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                title = match.group(1).replace('.', ' ').replace('_', ' ').strip()
                year = match.group(2)
                return {'title': title, 'year': year}

        # No year found, use entire filename as title
        title = name.replace('.', ' ').replace('_', ' ').strip()
        return {'title': title, 'year': None}

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
                'imdb_id': None  # Need to fetch from movie details
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
        print(f"📝 Parsed: {parsed['title']}" + (f" ({parsed['year']})" if parsed['year'] else ""))

        # Search by title and year
        movie = self.search_movie(parsed['title'], parsed['year'])

        if movie:
            print(f"✅ Found: {movie['title']} ({movie['year']})")
        else:
            print("❌ Movie not found")

        return movie
