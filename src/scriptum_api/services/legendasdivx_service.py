"""
LegendasDivx service
Integração com a API local do LegendasDivx
"""
import requests
from typing import List, Dict, Any, Optional


class LegendasDivxService:
    """Service para integração com API LegendasDivx"""

    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize LegendasDivx service

        Args:
            api_base_url: Base URL da API LegendasDivx local
        """
        self.api_base_url = api_base_url

    def _clean_query(self, query: str) -> str:
        """
        Clean query for better LegendasDivx search results
        Removes stop words and year
        """
        import re

        # Remove stop words at the beginning
        stop_words = ['the', 'a', 'an', 'o', 'a', 'os', 'as']
        words = query.split()

        # Remove stop words from beginning
        while words and words[0].lower() in stop_words:
            words = words[1:]

        # Remove year (4 digits at the end)
        if words and re.match(r'^\d{4}$', words[-1]):
            words = words[:-1]

        cleaned = ' '.join(words)
        print(f"🧹 Cleaned query: '{query}' → '{cleaned}'")
        return cleaned

    def search(self, query: str, language: str = 'pt-pt', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search subtitles on LegendasDivx

        Args:
            query: Search query (movie name)
            language: Language code (pt-pt, pt-br, en, es, fr)
            limit: Maximum results to return

        Returns:
            List of subtitle results
        """
        try:
            # Clean query for better results
            cleaned_query = self._clean_query(query)

            params = {
                'query': cleaned_query,
                'limit': limit,
            }

            # Mapear language code para o formato esperado
            if language in ['pt', 'pt-PT', 'pt-pt']:
                params['language'] = 'pt-pt'
            elif language in ['pt-BR', 'pt-br']:
                params['language'] = 'pt-br'

            response = requests.get(
                f"{self.api_base_url}/api/v1/search",
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"⚠️  LegendasDivx search failed: {response.status_code}")
                return []

            data = response.json()
            results = data.get('results', [])

            print(f"📦 LegendasDivx retornou {len(results)} resultados")

            # Converter para formato compatível com OpenSubtitles
            subtitles = []
            for item in results:
                subtitles.append({
                    'id': item.get('id'),
                    'file_id': item.get('id'),
                    'name': item.get('title', 'Unknown'),
                    'release': item.get('release', ''),
                    'language': self._normalize_language(item.get('language', 'pt-pt')),
                    'downloads': item.get('downloads', 0),
                    'rating': item.get('rating', 0) or 0,
                    'uploader': item.get('uploader', 'Unknown'),
                    'format': 'srt',
                    'source': 'legendasdivx',  # Identificador da fonte
                    'year': item.get('year'),
                })

            return subtitles

        except Exception as e:
            print(f"❌ Error searching LegendasDivx: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _normalize_language(self, lang: str) -> str:
        """Normaliza código de idioma"""
        mapping = {
            'pt-pt': 'Portuguese (PT)',
            'pt-br': 'Portuguese (BR)',
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
        }
        return mapping.get(lang, lang)

    def download_subtitle(self, subtitle_id: str) -> Optional[bytes]:
        """
        Download subtitle file by ID and extract from RAR if needed

        Args:
            subtitle_id: LegendasDivx subtitle ID

        Returns:
            Subtitle file content as bytes or None
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/download/{subtitle_id}",
                timeout=30
            )

            if response.status_code != 200:
                print(f"⚠️  Download failed: {response.status_code}")
                return None

            content = response.content
            print(f"✅ Downloaded from LegendasDivx ({len(content)} bytes)")

            # Check if it's a RAR file
            if content.startswith(b'Rar!'):
                print("📦 Extracting from RAR archive...")
                try:
                    import rarfile
                    import io
                    import tempfile

                    # Save to temporary file (rarfile needs a file path)
                    with tempfile.NamedTemporaryFile(suffix='.rar', delete=False) as tmp_rar:
                        tmp_rar.write(content)
                        tmp_rar_path = tmp_rar.name

                    # Extract SRT from RAR
                    with rarfile.RarFile(tmp_rar_path) as rf:
                        # Find first .srt file in the archive
                        srt_files = [f for f in rf.namelist() if f.lower().endswith('.srt')]
                        if srt_files:
                            print(f"   Found SRT: {srt_files[0]}")
                            content = rf.read(srt_files[0])
                            print(f"   ✅ Extracted SRT ({len(content)} bytes)")

                            # Detect and fix encoding
                            # LegendasDivx subtitles can be in various encodings
                            try:
                                # First try UTF-8
                                text = content.decode('utf-8')
                                print(f"   ℹ️  Already UTF-8")
                            except UnicodeDecodeError:
                                # Not UTF-8, try Latin-1
                                try:
                                    text = content.decode('iso-8859-1')
                                    content = text.encode('utf-8')
                                    print(f"   🔄 Converted encoding: ISO-8859-1 → UTF-8")
                                except:
                                    # Try Windows-1252 as fallback
                                    try:
                                        text = content.decode('windows-1252')
                                        content = text.encode('utf-8')
                                        print(f"   🔄 Converted encoding: Windows-1252 → UTF-8")
                                    except:
                                        print(f"   ⚠️  Could not detect encoding, keeping as-is")
                                        pass
                        else:
                            print("   ⚠️  No SRT file found in RAR")
                            return None

                    # Clean up temp file
                    import os
                    os.unlink(tmp_rar_path)

                except ImportError:
                    print("❌ rarfile library not installed. Install with: pip install rarfile")
                    return None
                except Exception as e:
                    print(f"❌ Error extracting RAR: {e}")
                    return None

            return content

        except Exception as e:
            print(f"❌ Error downloading from LegendasDivx: {e}")
            return None

    def is_available(self) -> bool:
        """Check if LegendasDivx API is available"""
        try:
            print(f"🔍 Checking LegendasDivx availability at: {self.api_base_url}/health")
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            is_ok = response.status_code == 200
            print(f"{'✅' if is_ok else '❌'} LegendasDivx API status: {response.status_code}")
            return is_ok
        except Exception as e:
            print(f"❌ LegendasDivx API not available: {e}")
            return False
