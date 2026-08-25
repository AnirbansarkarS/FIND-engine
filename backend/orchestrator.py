import asyncio
from typing import List
import httpx
from providers import SearchResult, WikipediaProvider, HackerNewsProvider, ArxivProvider

class SearchOrchestrator:
    def __init__(self):
        # Register the 3 basic search providers
        self.providers = [
            WikipediaProvider(),
            HackerNewsProvider(),
            ArxivProvider()
        ]

    async def search(self, query: str) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        async with httpx.AsyncClient() as client:
            # Create concurrent search tasks
            tasks = [provider.search(client, query) for provider in self.providers]
            
            # Execute concurrently, letting individual timeouts handle sluggishness
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Parse responses
            provider_lists = []
            for res in raw_results:
                if isinstance(res, list):
                    provider_lists.append(res)
                elif isinstance(res, Exception):
                    # Robust fallback in case of unhandled provider crashes
                    print(f"Orchestrator warning: Provider search raised an exception: {res}")
            
            # Interleave results for a balanced feed of Wikipedia, HN, and arXiv
            interleaved_results = []
            if provider_lists:
                max_length = max(len(l) for l in provider_lists)
                for i in range(max_length):
                    for provider_list in provider_lists:
                        if i < len(provider_list):
                            interleaved_results.append(provider_list[i])
                            
            return interleaved_results
