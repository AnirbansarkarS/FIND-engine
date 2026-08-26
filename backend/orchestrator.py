import asyncio
import urllib.parse
from typing import List
import httpx
from providers import (
    SearchResult,
    WikipediaProvider,
    HackerNewsProvider,
    ArxivProvider,
    DuckDuckGoProvider,
    GoogleProvider,
    BingProvider
)

class SearchOrchestrator:
    def __init__(self):
        # Register the 6 search providers
        self.providers = [
            WikipediaProvider(),
            HackerNewsProvider(),
            ArxivProvider(),
            DuckDuckGoProvider(),
            GoogleProvider(),
            BingProvider()
        ]

    def normalize_url(self, url: str) -> str:
        """
        Normalize a URL for deduplication comparisons:
        1. Strips schemes (http/https) and www.
        2. Strips trailing slashes.
        3. Strips UTM trackers (utm_source, etc.).
        4. Sorts remaining query parameters.
        """
        try:
            parsed = urllib.parse.urlparse(url.strip())
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
                
            path = parsed.path
            if path.endswith("/"):
                path = path[:-1]
                
            # Filter out common analytics query parameters
            query_params = urllib.parse.parse_qsl(parsed.query)
            filtered_params = []
            for k, v in query_params:
                k_lower = k.lower()
                if not (k_lower.startswith("utm_") or k_lower in {"gclid", "fbclid", "ref", "source"}):
                    filtered_params.append((k, v))
            
            # Sort remaining query parameters to ensure consistency
            query = ""
            if filtered_params:
                filtered_params.sort()
                query = "?" + urllib.parse.urlencode(filtered_params)
                
            return f"{netloc}{path}{query}"
        except Exception:
            # Fallback in case of parsing errors
            u = url.lower().strip()
            for prefix in ["https://", "http://", "www."]:
                if u.startswith(prefix):
                    u = u[len(prefix):]
            if u.endswith("/"):
                u = u[:-1]
            return u

    async def search(self, query: str) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        async with httpx.AsyncClient() as client:
            # Execute all queries concurrently
            tasks = [provider.search(client, query) for provider in self.providers]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            unique_results = {}
            
            for res in raw_results:
                if not isinstance(res, list):
                    continue
                
                for item in res:
                    norm_url = self.normalize_url(item.url)
                    
                    if norm_url in unique_results:
                        existing = unique_results[norm_url]
                        
                        # Merge sources
                        existing_sources = [s.strip() for s in existing.source.split(",")]
                        new_source = item.source.strip()
                        if new_source not in existing_sources:
                            existing_sources.append(new_source)
                            existing.source = ", ".join(existing_sources)
                        
                        # Retain richer description (longest snippet)
                        if len(item.snippet) > len(existing.snippet):
                            existing.snippet = item.snippet
                            
                        # Use newer published date if available
                        if item.published_date and (not existing.published_date or item.published_date > existing.published_date):
                            existing.published_date = item.published_date
                        
                        # Boost score: combine raw scores and add a multi-source boost
                        existing.raw_score = (existing.raw_score or 0.0) + (item.raw_score or 0.0) + 3.0
                    else:
                        # Instantiate new record to avoid mutating cache
                        unique_results[norm_url] = SearchResult(
                            title=item.title,
                            url=item.url,
                            domain=item.domain,
                            snippet=item.snippet,
                            source=item.source,
                            published_date=item.published_date,
                            raw_score=item.raw_score
                        )
            
            # Sort results by raw_score descending
            aggregated = list(unique_results.values())
            aggregated.sort(key=lambda x: x.raw_score or 0.0, reverse=True)
            
            return aggregated
