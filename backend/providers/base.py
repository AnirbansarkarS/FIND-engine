from abc import ABC, abstractmethod
from typing import List, Optional
import urllib.parse
import httpx
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    domain: str
    snippet: str
    source: str
    published_date: Optional[str] = None
    raw_score: Optional[float] = 0.0

class BaseProvider(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        """
        Asynchronously search the provider and return a list of SearchResult objects.
        """
        pass

    def extract_domain(self, url: str) -> str:
        """
        Extract root domain from a given URL (stripping www.).
        """
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc or parsed.path.split("/")[0]
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.lower()
        except Exception:
            return "unknown"
