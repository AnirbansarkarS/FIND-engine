from typing import List
import html
import httpx
from .base import BaseProvider, SearchResult

class HackerNewsProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="hackernews")
        self.api_url = "https://hn.algolia.com/api/v1/search"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": 10
        }
        
        try:
            response = await client.get(self.api_url, params=params, timeout=4.0)
            response.raise_for_status()
            data = response.json()
            
            hits = data.get("hits", [])
            results = []
            for idx, hit in enumerate(hits):
                title = hit.get("title") or hit.get("story_title")
                if not title:
                    continue
                
                object_id = hit.get("objectID")
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
                
                story_text = hit.get("story_text")
                points = hit.get("points") or 0
                comments = hit.get("num_comments")
                author = hit.get("author")
                published_date = hit.get("created_at")  # Algolia returns ISO string
                
                # Format description cleanly
                meta_parts = []
                if points:
                    meta_parts.append(f"{points} points")
                if comments is not None:
                    meta_parts.append(f"{comments} comments")
                if author:
                    meta_parts.append(f"by {author}")
                    
                meta_str = " | ".join(meta_parts)
                
                if story_text:
                    clean_text = html.unescape(story_text).replace("<p>", " ").replace("</p>", "")
                    snippet = f"{clean_text[:200]}... ({meta_str})" if len(clean_text) > 200 else f"{clean_text} ({meta_str})"
                else:
                    snippet = f"Discussion on Hacker News. {meta_str}"
                
                domain = self.extract_domain(url)
                
                # Position-based score (10.0 to 1.0) + popularity bonus (up to 5.0 points)
                position_score = float(max(1.0, 10.0 - idx))
                popularity_bonus = min(5.0, points / 100.0)
                raw_score = position_score + popularity_bonus
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        domain=domain,
                        snippet=snippet,
                        source=self.name,
                        published_date=published_date,
                        raw_score=raw_score
                    )
                )
            return results
        except Exception as e:
            print(f"Hacker News search failed: {e}")
            return []
