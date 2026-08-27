import os
import urllib.parse
from typing import List
import httpx
from bs4 import BeautifulSoup
from .base import BaseProvider, SearchResult

class GoogleProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="google")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cx = os.getenv("GOOGLE_CX")
        self.api_url = "https://www.googleapis.com/customsearch/v1"
        self.scrape_url = "https://www.google.com/search"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        # If API credentials are set, use the official JSON API
        if self.api_key and self.cx:
            return await self._search_api(client, query)
        else:
            # Fallback to keyless HTML scraper
            return await self._search_html(client, query)

    async def _search_api(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 10
        }
        
        try:
            response = await client.get(self.api_url, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            results = []
            
            for idx, item in enumerate(items):
                title = item.get("title", "")
                url = item.get("link", "")
                snippet = item.get("snippet", "")
                
                published_date = None
                pagemap = item.get("pagemap", {})
                metatags = pagemap.get("metatags", [])
                if metatags and isinstance(metatags, list) and len(metatags) > 0:
                    meta = metatags[0]
                    published_date = (
                        meta.get("article:published_time") or 
                        meta.get("datepublished") or 
                        meta.get("pubdate") or
                        meta.get("og:pubdate")
                    )
                
                domain = self.extract_domain(url)
                raw_score = float(max(1.0, 10.0 - idx))
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        domain=domain,
                        snippet=snippet or "No description available.",
                        source=self.name,
                        published_date=published_date,
                        raw_score=raw_score
                    )
                )
            return results
        except Exception as e:
            print(f"Google API search failed, falling back to HTML: {e}")
            return await self._search_html(client, query)

    async def _search_html(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {
            "q": query,
            "gbv": "1"  # Force Google Basic Version for easy no-JS parsing
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        try:
            response = await client.get(self.scrape_url, params=params, headers=headers, timeout=5.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Google gbv=1 search results links start with /url?q=
            links = soup.find_all("a", href=lambda h: h and h.startswith("/url?q="))
            results = []
            seen_urls = set()
            
            for link in links:
                href = link.get("href", "")
                
                # Extract and decode target URL
                try:
                    parsed_href = urllib.parse.urlparse(href)
                    queries = urllib.parse.parse_qs(parsed_href.query)
                    target_url = queries.get("q", [""])[0]
                except Exception:
                    continue
                
                # Exclude Google self-links
                if not target_url or any(x in target_url for x in ["accounts.google.com", "support.google.com", "google.com/search"]):
                    continue
                    
                if target_url in seen_urls:
                    continue
                seen_urls.add(target_url)
                
                h3 = link.find("h3")
                title = h3.get_text(strip=True) if h3 else link.get_text(strip=True)
                
                # Extract Snippet (traverse parent nodes to locate sibling text block)
                snippet = ""
                parent = link.find_parent("div")
                if parent:
                    grandparent = parent.parent
                    if grandparent:
                        # Standard class in basic Google
                        desc_div = grandparent.find("div", class_=lambda c: c and "s3v9rd" in c)
                        if desc_div:
                            snippet = desc_div.get_text(strip=True)
                        else:
                            # Sibling text block fallback
                            for elem in grandparent.find_all(["div", "span"]):
                                txt = elem.get_text(strip=True)
                                if txt and txt != title and len(txt) > 30 and not txt.startswith("http"):
                                    snippet = txt
                                    break
                
                if snippet:
                    # Clean up Google cached labels
                    snippet = snippet.replace("Cached", "").strip()
                    
                domain = self.extract_domain(target_url)
                raw_score = float(max(1.0, 10.0 - len(results)))
                
                results.append(
                    SearchResult(
                        title=title,
                        url=target_url,
                        domain=domain,
                        snippet=snippet or "No description available.",
                        source=self.name,
                        published_date=None,
                        raw_score=raw_score
                    )
                )
                
                if len(results) >= 10:
                    break
                    
            return results
        except Exception as e:
            print(f"Google HTML scraper failed: {e}")
            return []
