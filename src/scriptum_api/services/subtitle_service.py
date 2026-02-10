"""
Subtitle service
Handles OpenSubtitles API integration for subtitle search and download
"""
import requests
import gzip
import base64
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from difflib import SequenceMatcher


class SubtitleService:
    """Service for subtitle operations with OpenSubtitles"""

    def __init__(self, api_key: str):
        """
        Initialize subtitle service

        Args:
            api_key: OpenSubtitles API key
        """
        self.api_key = api_key
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.user_agent = "Scriptum v2.1"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'Api-Key': self.api_key,
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json'
        }

    def _calculate_relevance(self, query: str, movie_name: str) -> float:
        """
        Calculate relevance score between query and movie name

        Args:
            query: Search query
            movie_name: Movie name from result

        Returns:
            Relevance score (0.0 - 1.0)
        """
        # Common words to ignore
        STOP_WORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'of', 'to', 'in', 'for', 'on', 'with'}

        # Normalize strings
        query_norm = query.lower().strip()
        movie_norm = movie_name.lower().strip()

        # Remove year from both for comparison
        query_clean = re.sub(r'\b(19|20)\d{2}\b', '', query_norm).strip()
        movie_clean = re.sub(r'\b(19|20)\d{2}\b', '', movie_norm).strip()

        # Extract main keywords (words longer than 2 chars, excluding stop words)
        query_words = set([w for w in re.findall(r'\w+', query_clean) if len(w) > 2 and w not in STOP_WORDS])
        movie_words = set([w for w in re.findall(r'\w+', movie_clean) if len(w) > 2 and w not in STOP_WORDS])

        if not query_words:
            return 0.5

        # Calculate word overlap
        common_words = query_words & movie_words
        word_overlap = len(common_words) / len(query_words) if query_words else 0

        # Calculate sequence similarity (only on meaningful words)
        query_meaningful = ' '.join(sorted(query_words))
        movie_meaningful = ' '.join(sorted(movie_words))
        sequence_sim = SequenceMatcher(None, query_meaningful, movie_meaningful).ratio()

        # Combined score (heavily favor word overlap for exact matches)
        score = (word_overlap * 0.8) + (sequence_sim * 0.2)

        return score

    def _filter_and_sort_results(self, results: List[Dict[str, Any]], query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Filter and sort results by relevance

        Args:
            results: Raw subtitle results
            query: Original search query
            limit: Maximum results to return

        Returns:
            Filtered and sorted results
        """
        # Calculate relevance for each result
        scored_results = []
        for result in results:
            movie_name = result.get('name', '')
            relevance = self._calculate_relevance(query, movie_name)

            # Only keep results with decent relevance (>60%)
            if relevance >= 0.6:
                # Calculate combined score (relevance + popularity)
                downloads = result.get('downloads', 0)
                rating = result.get('rating', 0)

                # Normalize downloads to 0-1 scale (log scale for better distribution)
                import math
                download_score = min(1.0, math.log10(downloads + 1) / 5.0) if downloads > 0 else 0

                # Normalize rating to 0-1 scale
                rating_score = rating / 10.0 if rating > 0 else 0

                # Combined score: 60% relevance, 25% downloads, 15% rating
                combined_score = (relevance * 0.6) + (download_score * 0.25) + (rating_score * 0.15)

                scored_results.append({
                    **result,
                    '_relevance': relevance,
                    '_score': combined_score
                })

        # Sort by combined score (descending)
        scored_results.sort(key=lambda x: x['_score'], reverse=True)

        # Remove scoring metadata and return top results
        filtered = [{k: v for k, v in r.items() if not k.startswith('_')} for r in scored_results[:limit]]

        print(f"🎯 Filtradas {len(filtered)} de {len(results)} legendas (relevância mínima: 60%)")

        return filtered

    def search_by_query(self, query: str, language: str = 'pt', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search subtitles by query string

        Args:
            query: Search query (movie name)
            language: Language code (pt, en, etc)
            limit: Maximum results to return

        Returns:
            List of subtitle results
        """
        if not self.api_key:
            print("⚠️  OpenSubtitles API key not configured")
            return []

        try:
            params = {
                'query': query,
                'languages': language,
            }

            response = requests.get(
                f"{self.base_url}/subtitles",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️  OpenSubtitles search failed: {response.status_code}")
                return []

            data = response.json()
            results = data.get('data', [])

            print(f"📦 API retornou {len(results)} resultados brutos")

            subtitles = []
            for item in results:
                attributes = item.get('attributes', {})
                files = attributes.get('files', [])

                # Get file_id from files if available, otherwise use item id
                file_id = files[0].get('file_id') if files else str(item.get('id', ''))

                # Extract feature details for better display
                feature = attributes.get('feature_details', {})
                movie_name = feature.get('movie_name', attributes.get('release', 'Unknown'))

                subtitles.append({
                    'id': file_id,
                    'file_id': file_id,
                    'name': movie_name,
                    'language': attributes.get('language', 'unknown'),
                    'downloads': attributes.get('download_count', 0),
                    'rating': round(attributes.get('ratings', 0), 1),
                    'uploader': attributes.get('uploader', {}).get('name', 'Unknown'),
                    'format': attributes.get('format', 'srt'),
                    'release': attributes.get('release', ''),
                    'feature_details': feature,
                })

            # Filter and sort by relevance
            filtered_subtitles = self._filter_and_sort_results(subtitles, query, limit)

            print(f"✅ Retornadas {len(filtered_subtitles)} legendas relevantes")
            return filtered_subtitles

        except Exception as e:
            print(f"❌ Error searching subtitles: {e}")
            import traceback
            traceback.print_exc()
            return []

    def search_by_hash(self, file_hash: str, file_size: int, language: str = 'pt') -> List[Dict[str, Any]]:
        """
        Search subtitles by video file hash (most accurate)

        Args:
            file_hash: OpenSubtitles hash of video file
            file_size: Video file size in bytes
            language: Language code

        Returns:
            List of subtitle results
        """
        if not self.api_key:
            print("⚠️  OpenSubtitles API key not configured")
            return []

        try:
            params = {
                'moviehash': file_hash,
                'languages': language,
            }

            response = requests.get(
                f"{self.base_url}/subtitles",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️  OpenSubtitles hash search failed: {response.status_code}")
                return []

            data = response.json()
            results = data.get('data', [])

            subtitles = []
            for item in results:
                attributes = item.get('attributes', {})
                files = attributes.get('files', [])

                if not files:
                    continue

                file_info = files[0]

                subtitles.append({
                    'file_id': file_info.get('file_id'),
                    'name': attributes.get('release', 'Unknown'),
                    'language': attributes.get('language', 'unknown'),
                    'downloads': attributes.get('download_count', 0),
                    'rating': round(attributes.get('ratings', 0), 1),
                    'uploader': attributes.get('uploader', {}).get('name', 'Unknown'),
                    'feature_details': attributes.get('feature_details', {}),
                })

            return subtitles

        except Exception as e:
            print(f"❌ Error searching by hash: {e}")
            return []

    def download_subtitle(self, file_id: int) -> Optional[bytes]:
        """
        Download subtitle file by file ID

        Args:
            file_id: OpenSubtitles file ID

        Returns:
            Subtitle file content as bytes or None
        """
        if not self.api_key:
            print("⚠️  OpenSubtitles API key not configured")
            return None

        try:
            # Step 1: Request download link
            payload = {
                'file_id': file_id
            }

            print(f"DEBUG: Sending request to {self.base_url}/download")
            print(f"DEBUG: Payload: {payload}")
            print(f"DEBUG: Headers: {self._get_headers()}")

            response = requests.post(
                f"{self.base_url}/download",
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text[:200]}")

            if response.status_code != 200:
                print(f"⚠️  Download request failed: {response.status_code}")
                print(f"⚠️  Response: {response.text}")
                return None

            data = response.json()
            download_link = data.get('link')

            if not download_link:
                print("❌ No download link provided")
                return None

            # Step 2: Download the file
            print(f"DEBUG: Downloading from link: {download_link[:100]}...")
            download_response = requests.get(
                download_link,
                headers={'User-Agent': self.user_agent},
                timeout=30
            )

            if download_response.status_code != 200:
                print(f"⚠️  Download failed: {download_response.status_code}")
                print(f"⚠️  Download response: {download_response.text[:200]}")
                return None

            # The file is typically gzipped
            try:
                content = gzip.decompress(download_response.content)
            except:
                # If not gzipped, use as-is
                content = download_response.content

            print(f"✅ Subtitle downloaded ({len(content)} bytes)")
            return content

        except Exception as e:
            print(f"❌ Error downloading subtitle: {e}")
            return None

    @staticmethod
    def calculate_hash(video_path: Path) -> Optional[str]:
        """
        Calculate OpenSubtitles hash for video file

        Args:
            video_path: Path to video file

        Returns:
            Hash string or None
        """
        try:
            longlongformat = 'q'  # long long
            bytesize = 8  # 8 bytes = 64 bits

            filesize = video_path.stat().st_size

            if filesize < 65536 * 2:
                return None

            hash_value = filesize

            with open(video_path, 'rb') as f:
                # Read first 64kb
                for _ in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = __import__('struct').unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value &= 0xFFFFFFFFFFFFFFFF  # Stay as 64-bit

                # Read last 64kb
                f.seek(max(0, filesize - 65536), 0)
                for _ in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = __import__('struct').unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value &= 0xFFFFFFFFFFFFFFFF

            return "%016x" % hash_value

        except Exception as e:
            print(f"❌ Error calculating hash: {e}")
            return None

    def quick_search(self, filename: str, language: str = 'pt', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Quick subtitle search using only filename (no video upload needed)

        Args:
            filename: Video filename
            language: Language code
            limit: Maximum results

        Returns:
            List of subtitle results
        """
        # Parse filename to extract movie name
        from pathlib import Path
        import re

        basename = Path(filename).stem

        # Remove common tags
        clean_name = re.sub(r'[\.\-_]', ' ', basename)
        clean_name = re.sub(r'\b(1080p|720p|480p|2160p|4K|BluRay|WEB-DL|WEBRip|HDTV|DVDRip|BRRip|x264|x265|HEVC|AAC|AC3|DTS|YIFY|RARBG|AMZN)\b', '', clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()

        # Extract year if present
        year_match = re.search(r'\b(19|20)\d{2}\b', clean_name)
        if year_match:
            year = year_match.group(0)
            clean_name = clean_name.replace(year, '').strip()
            query = f"{clean_name} {year}"
        else:
            query = clean_name

        print(f"🔍 Quick search for: {query}")

        return self.search_by_query(query, language, limit)
