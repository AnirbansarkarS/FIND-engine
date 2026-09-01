import logging
from typing import List
import httpx
from providers.base import BaseProvider, SearchResult
from database import get_sessionmaker

logger = logging.getLogger("findengine.providers.crawler")

class LocalCrawlerProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="Local Crawler")

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        """
        Query the local inverted index / full-text database for crawled documents.
        Does NOT contact any external API.
        """
        if not query or not query.strip():
            return []

        try:
            from index_engine import index_engine
            sm = get_sessionmaker()
            async with sm() as db:
                results = await index_engine.search_index(db, query, limit=30)
                logger.info(f"LocalCrawlerProvider retrieved {len(results)} matches for '{query}'")
                return results
        except Exception as e:
            logger.error(f"LocalCrawlerProvider search error: {e}")
            return []
