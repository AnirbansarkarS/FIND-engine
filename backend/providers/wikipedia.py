import re
from typing import List
import httpx
from .base import BaseProvider, SearchResult

class WikipediaProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="wikipedia")
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.html_tag_re = re.compile(r"<[^>]+>")

    def _clean_snippet(self, text: str) -> str:
        # Strip HTML tags like <span class="searchmatch">
        cleaned = self.html_tag_re.sub("", text)
        # Decode HTML entities if any (like &quot; or &amp;)
        import html
        return html.unescape(cleaned).strip()

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 10  # Return up to 10 results
        }
        
        try:
            headers = {
                "User-Agent": "FIND-engine/1.0 (contact: sanirban.sarkar.99@gmail.com; user-agent-header)"
            }
            response = await client.get(self.api_url, params=params, headers=headers, timeout=4.0)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get("query", {}).get("search", [])
            results = []
            for item in search_results:
                page_id = item.get("pageid")
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                url = f"https://en.wikipedia.org/?curid={page_id}"
                description = self._clean_snippet(snippet)
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        description=description or "No description available.",
                        source=self.name
                    )
                )
            return results
        except Exception as e:
            # Log error internally and return empty list to remain robust
            print(f"Wikipedia search failed: {e}")
            return []
