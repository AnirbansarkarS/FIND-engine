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
            "tags": "story",  # Focus on stories/articles rather than comments
            "hitsPerPage": 10
        }
        
        try:
            response = await client.get(self.api_url, params=params, timeout=4.0)
            response.raise_for_status()
            data = response.json()
            
            hits = data.get("hits", [])
            results = []
            for hit in hits:
                title = hit.get("title") or hit.get("story_title")
                if not title:
                    continue
                
                object_id = hit.get("objectID")
                # Use external URL if available, fallback to HN discussion page
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
                
                story_text = hit.get("story_text")
                points = hit.get("points")
                comments = hit.get("num_comments")
                author = hit.get("author")
                
                # Format description cleanly
                meta_parts = []
                if points is not None:
                    meta_parts.append(f"{points} points")
                if comments is not None:
                    meta_parts.append(f"{comments} comments")
                if author:
                    meta_parts.append(f"by {author}")
                    
                meta_str = " | ".join(meta_parts)
                
                if story_text:
                    # Clean up HTML entities in story text
                    clean_text = html.unescape(story_text).replace("<p>", " ").replace("</p>", "")
                    description = f"{clean_text[:200]}... ({meta_str})" if len(clean_text) > 200 else f"{clean_text} ({meta_str})"
                else:
                    description = f"Discussion on Hacker News. {meta_str}"
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source=self.name
                    )
                )
            return results
        except Exception as e:
            print(f"Hacker News search failed: {e}")
            return []
