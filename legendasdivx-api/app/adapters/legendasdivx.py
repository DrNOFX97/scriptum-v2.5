import httpx
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import time
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models.subtitle import SubtitleSearchResult, Language
from app.config import get_settings
from app.adapters.base import SubtitleProvider
import logging

logger = logging.getLogger(__name__)

class LegendasDivxAdapter(SubtitleProvider):
    """Adapter para legendasdivx.pt"""
    
    BASE_URL = "https://www.legendasdivx.pt"
    LOGIN_URL = f"{BASE_URL}/forum/ucp.php?mode=login"
    SEARCH_URL = f"{BASE_URL}/modules.php"
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        self._last_request_time = 0
        
    async def _ensure_session(self):
        """Garante que temos uma sessão válida"""
        if self.session is None:
            await self._login()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _login(self):
        """Faz login no site"""
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
            },
            follow_redirects=True,
            timeout=30.0
        )
        
        # Primeiro GET para obter cookies
        login_page = await self.session.get(self.LOGIN_URL)
        soup = BeautifulSoup(login_page.text, 'lxml')
        
        # Extrair sid do form
        sid_input = soup.find("input", {"name": "sid"})
        sid = sid_input["value"] if sid_input else ""
        
        # POST login
        login_data = {
            "username": self.settings.legendasdivx_user,
            "password": self.settings.legendasdivx_pass,
            "autologin": "on",
            "viewonline": "on",
            "redirect": "./index.php",
            "sid": sid,
            "login": "Entrar",
        }
        
        response = await self.session.post(self.LOGIN_URL, data=login_data)
        
        # Verificar se login foi bem sucedido
        if "logout" not in response.text.lower():
            raise Exception("Login falhou - verificar credenciais")
        
        logger.info("Login bem sucedido no LegendasDivx")
    
    async def _rate_limit(self):
        """Implementa rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.settings.request_delay_seconds:
            sleep_time = self.settings.request_delay_seconds - time_since_last
            logger.debug(f"Rate limiting: aguardando {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def search(self, query: str, language: Optional[Language] = None) -> List[SubtitleSearchResult]:
        """Pesquisa legendas no site"""
        await self._ensure_session()
        await self._rate_limit()
        
        search_params = {
            "name": "Downloads",
            "file": "jz",
            "d_op": "search",
            "query": query,
        }
        
        if language:
             lang_code = self._map_language(language)
             if lang_code != "0":
                 search_params["form_cat"] = lang_code
        
        response = await self.session.get(self.SEARCH_URL, params=search_params)
        
        return self._parse_search_results(response.text)
    
    def _map_language(self, language: Language) -> str:
        """Mapeia Language enum para código do site"""
        mapping = {
            Language.PT_PT: "28",
            Language.PT_BR: "29", 
        }
        return mapping.get(language, "0")
    
    def _parse_search_results(self, html: str) -> List[SubtitleSearchResult]:
        """Parser dos resultados de pesquisa"""
        soup = BeautifulSoup(html, 'lxml')
        results = []
        
        # Encontrar caixas de resultados
        sub_boxes = soup.find_all("div", {"class": "sub_box"})
        
        for box in sub_boxes:
            try:
                # 1. ID e Download Link
                footer = box.find("div", {"class": "sub_footer"})
                if not footer: continue
                
                download_link = footer.find("a", {"class": "sub_download"})
                if not download_link: continue
                
                href = download_link.get("href", "")
                subtitle_id_match = re.search(r"lid=(\d+)", href)
                if not subtitle_id_match: continue
                subtitle_id = subtitle_id_match.group(1)
                
                # 2. Header info (Title, Uploader, Year)
                header = box.find("div", {"class": "sub_header"})
                title = "Unknown"
                uploader = "Unknown"
                year = None
                
                if header:
                    header_text = header.get_text().strip()
                    # Try to extract "Title (Year)"
                    title_match = re.search(r"^(.*?)\s*\((\d{4})\)", header_text)
                    if title_match:
                        title = title_match.group(1).strip()
                        year = int(title_match.group(2))
                    else:
                        title = header_text.split("-")[0].strip()

                    # Uploader
                    uploader_elem = header.find("a", href=lambda x: x and "user_info" in x.lower())
                    if uploader_elem:
                        uploader = uploader_elem.get_text().strip()

                # 3. Main info (Language, Downloads, Release)
                main_table = box.find("table", {"class": "sub_main"})
                language = Language.PT_PT
                downloads = 0
                release = ""
                
                if main_table:
                    # Language
                    img = main_table.find("img", src=lambda x: x and ("brazil" in x.lower() or "portugal" in x.lower() or "uk" in x.lower() or "spain" in x.lower()))
                    if img:
                        src = img.get("src", "").lower()
                        if "brazil" in src: language = Language.PT_BR
                        elif "portugal" in src: language = Language.PT_PT
                        elif "uk" in src or "english" in src: language = Language.EN
                        elif "spain" in src: language = Language.ES

                    # Downloads/Hits
                    hits_match = re.search(r"Hits:\s*(\d+)", main_table.get_text())
                    if hits_match:
                        downloads = int(hits_match.group(1))
                        
                    # Description / Release
                    desc_td = main_table.find("td", {"class": "td_desc"})
                    if desc_td:
                        desc_text = desc_td.get_text(" ", strip=True)
                        # Try to find something that looks like a release
                        release_match = re.search(r"([A-Za-z0-9\.\-_]+\.(1080p|720p|HDTV|BDRip|BluRay|WEB-DL|DVDRip)[A-Za-z0-9\.\-_]*)", desc_text, re.IGNORECASE)
                        if release_match:
                            release = release_match.group(1)
                        else:
                            # Fallback: take a snippet
                            release = desc_text[:50].strip() + "..." if len(desc_text) > 50 else desc_text

                result = SubtitleSearchResult(
                    id=subtitle_id,
                    title=title,
                    release=release,
                    language=language,
                    uploader=uploader,
                    downloads=downloads,
                    year=year,
                    source="legendasdivx"
                )
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Erro ao processar item: {e}")
                continue
        
        return results
    
    def _detect_language(self, img_src: str) -> Language:
        """Detecta idioma pela imagem da bandeira"""
        if "portugal" in img_src.lower():
            return Language.PT_PT
        elif "brasil" in img_src.lower():
            return Language.PT_BR
        elif "english" in img_src.lower() or "uk" in img_src.lower():
            return Language.EN
        elif "spain" in img_src.lower():
            return Language.ES
        elif "france" in img_src.lower():
            return Language.FR
        return Language.PT_PT
    
    async def download(self, subtitle_id: str) -> bytes:
        """Download de uma legenda específica"""
        await self._ensure_session()
        await self._rate_limit()
        
        # URL correta baseada no HTML: modules.php?name=Downloads&d_op=getit&lid=XXX
        params = {
            "name": "Downloads",
            "d_op": "getit",
            "lid": subtitle_id
        }
        
        response = await self.session.get(self.SEARCH_URL, params=params, follow_redirects=True)
        
        if response.status_code != 200:
            raise Exception(f"Download falhou: {response.status_code}")
            
        # Verificar se é um ficheiro zip/rar ou página de erro
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" in content_type:
            if "login" in response.text.lower():
                raise Exception("Sessão de login inválida durante download")
            elif "erro" in response.text.lower():
                raise Exception("Erro no site ao baixar legenda")
        
        return response.content
    
    async def get_details(self, subtitle_id: str) -> Dict[str, Any]:
        """Obtém detalhes de uma legenda"""
        await self._ensure_session()
        await self._rate_limit()
        
        details_url = f"{self.BASE_URL}/modules.php?name=downloads&file=detalhes&lid={subtitle_id}"
        
        response = await self.session.get(details_url)
        
        # Parse detalhes (implementar conforme estrutura da página)
        # Por agora retorna dict básico
        return {"id": subtitle_id, "fetched": True}
