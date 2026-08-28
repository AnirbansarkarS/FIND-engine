import asyncio
import math
import urllib.parse
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from providers import (
    SearchResult,
    WikipediaProvider,
    HackerNewsProvider,
    ArxivProvider,
    DuckDuckGoProvider,
    GoogleProvider,
    BingProvider,
    YahooProvider,
    ExaProvider
)

class SearchOrchestrator:
    def __init__(self):
        # Register all 8 search providers (including Exa AI)
        self.providers = [
            WikipediaProvider(),
            HackerNewsProvider(),
            ArxivProvider(),
            DuckDuckGoProvider(),
            GoogleProvider(),
            BingProvider(),
            YahooProvider(),
            ExaProvider()
        ]


    def normalize_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url.strip())
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
                
            path = parsed.path
            if path.endswith("/"):
                path = path[:-1]
                
            query_params = urllib.parse.parse_qsl(parsed.query)
            filtered_params = []
            for k, v in query_params:
                k_lower = k.lower()
                if not (k_lower.startswith("utm_") or k_lower in {"gclid", "fbclid", "ref", "source"}):
                    filtered_params.append((k, v))
            
            query = ""
            if filtered_params:
                filtered_params.sort()
                query = "?" + urllib.parse.urlencode(filtered_params)
                
            return f"{netloc}{path}{query}"
        except Exception:
            u = url.lower().strip()
            for prefix in ["https://", "http://", "www."]:
                if u.startswith(prefix):
                    u = u[len(prefix):]
            if u.endswith("/"):
                u = u[:-1]
            return u

    def compute_ranking(
        self, 
        item: SearchResult, 
        query: str, 
        category_preference: Optional[str] = None
    ) -> float:
        """
        Ranking Engine Formula:
        Final Score = 0.30 * provider_score 
                    + 0.25 * text_relevance 
                    + 0.20 * cross_engine_agreement 
                    + 0.10 * freshness 
                    + 0.10 * domain_quality 
                    + 0.05 * personalization
        """
        # 1. Provider Score (0.0 to 1.0)
        provider_score = min(1.0, (item.raw_score or 1.0) / 10.0)
        
        # 2. Text Relevance (title + snippet keyword frequency)
        query_words = [w.lower() for w in query.split() if len(w) > 1]
        if query_words:
            title_lower = item.title.lower()
            snippet_lower = item.snippet.lower()
            
            title_hits = sum(1 for w in query_words if w in title_lower)
            snippet_hits = sum(1 for w in query_words if w in snippet_lower)
            
            relevance_raw = (title_hits * 3.0 + snippet_hits * 1.0) / (len(query_words) * 3.0)
            text_relevance = min(1.0, relevance_raw)
        else:
            text_relevance = 0.50
            
        # 3. Cross-Engine Agreement
        sources_list = [s.strip() for s in item.source.split(",") if s.strip()]
        num_sources = len(sources_list)
        cross_engine_agreement = min(1.0, (num_sources - 1) / 3.0) if num_sources > 1 else 0.0
        
        # 4. Freshness Score
        freshness = 0.20
        if item.published_date:
            try:
                date_str = item.published_date.replace("Z", "+00:00")
                pub_date = datetime.fromisoformat(date_str)
                now = datetime.now(timezone.utc)
                age_days = max(0, (now - pub_date).days)
                freshness = max(0.1, math.exp(-age_days / 180.0))
            except Exception:
                freshness = 0.40
                
        # 5. Domain Quality Authority Index
        authoritative_domains = {
            "wikipedia.org": 1.0,
            "en.wikipedia.org": 1.0,
            "arxiv.org": 0.95,
            "nature.com": 0.95,
            "github.com": 0.90,
            "phys.org": 0.90,
            "news.ycombinator.com": 0.85,
            "stackoverflow.com": 0.85,
            "python.org": 0.90,
            "developer.mozilla.org": 0.95
        }
        domain_quality = authoritative_domains.get(item.domain.lower(), 0.70)
        
        # 6. Personalization Bias
        personalization = 0.50
        if category_preference:
            pref = category_preference.lower()
            src_list = [s.lower() for s in sources_list]
            if pref == "tech" and any(s in src_list for s in ["hackernews", "arxiv", "exa"]):
                personalization = 1.0
            elif pref == "academic" and any(s in src_list for s in ["arxiv", "wikipedia", "exa"]):
                personalization = 1.0
            elif pref == "news" and any(s in src_list for s in ["hackernews", "yahoo", "google", "bing", "duckduckgo", "exa"]):
                personalization = 1.0


        final_score = (
            0.30 * provider_score +
            0.25 * text_relevance +
            0.20 * cross_engine_agreement +
            0.10 * freshness +
            0.10 * domain_quality +
            0.05 * personalization
        )
        
        return round(final_score, 4)

    async def search(self, query: str, category: Optional[str] = None) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        async with httpx.AsyncClient() as client:
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
                        
                        existing_sources = [s.strip() for s in existing.source.split(",")]
                        new_source = item.source.strip()
                        if new_source not in existing_sources:
                            existing_sources.append(new_source)
                            existing.source = ", ".join(existing_sources)
                        
                        if len(item.snippet) > len(existing.snippet):
                            existing.snippet = item.snippet
                            
                        if item.published_date and (not existing.published_date or item.published_date > existing.published_date):
                            existing.published_date = item.published_date
                    else:
                        unique_results[norm_url] = SearchResult(
                            title=item.title,
                            url=item.url,
                            domain=item.domain,
                            snippet=item.snippet,
                            source=item.source,
                            published_date=item.published_date,
                            raw_score=item.raw_score
                        )
            
            # Compute custom ranking engine score for all deduplicated entries
            aggregated = list(unique_results.values())
            for item in aggregated:
                item.raw_score = self.compute_ranking(item, query, category_preference=category)
                
            # Re-rank strictly by our engine's final score
            aggregated.sort(key=lambda x: x.raw_score or 0.0, reverse=True)
            
            return aggregated
