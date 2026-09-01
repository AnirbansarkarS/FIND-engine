import os
import re
import asyncio
import hashlib
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Optional
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, func, update, delete
from database import get_sessionmaker, CrawledDocument, CrawlQueue, CrawlStat

logger = logging.getLogger("findengine.crawler")

# Preset Seed URL Packs
PRESET_SEED_PACKS = {
    "wikipedia": [
        "https://en.wikipedia.org/wiki/Main_Page",
        "https://en.wikipedia.org/wiki/Computer_science",
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://en.wikipedia.org/wiki/Web_search_engine",
        "https://en.wikipedia.org/wiki/Information_retrieval"
    ],
    "documentation": [
        "https://docs.python.org/3/",
        "https://developer.mozilla.org/en-US/docs/Web",
        "https://react.dev/learn",
        "https://fastapi.tiangolo.com/",
        "https://sqlite.org/docs.html"
    ],
    "tech_news": [
        "https://news.ycombinator.com/",
        "https://arxiv.org/list/cs/recent",
        "https://slashdot.org/",
        "https://lobste.rs/"
    ],
    "universities": [
        "https://www.mit.edu/",
        "https://www.stanford.edu/",
        "https://www.harvard.edu/"
    ],
    "open_source": [
        "https://github.com/explore",
        "https://pypi.org/",
        "https://crates.io/"
    ]
}

class UrlFrontier:
    @staticmethod
    def hash_url(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> Optional[str]:
        try:
            if base_url:
                url = urllib.parse.urljoin(base_url, url)
            
            parsed = urllib.parse.urlparse(url.strip())
            if parsed.scheme not in ("http", "https"):
                return None
            
            # Skip common non-HTML file extensions
            path_lower = parsed.path.lower()
            skip_extensions = (
                ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".css", ".js", 
                ".pdf", ".zip", ".tar", ".gz", ".mp3", ".mp4", ".avi", ".exe", ".dmg"
            )
            if any(path_lower.endswith(ext) for ext in skip_extensions):
                return None

            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]

            path = parsed.path
            if path.endswith("/") and len(path) > 1:
                path = path[:-1]

            # Filter out tracking query parameters
            query_params = urllib.parse.parse_qsl(parsed.query)
            filtered_params = [
                (k, v) for k, v in query_params 
                if not (k.lower().startswith("utm_") or k.lower() in {"gclid", "fbclid", "ref", "source"})
            ]
            
            query = ""
            if filtered_params:
                filtered_params.sort()
                query = "?" + urllib.parse.urlencode(filtered_params)

            return f"{parsed.scheme}://{netloc}{path}{query}"
        except Exception:
            return None

    @staticmethod
    def extract_domain(url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain or "unknown"
        except Exception:
            return "unknown"


class ContentExtractor:
    @staticmethod
    def extract(html_content: str, page_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract Title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.h1:
            title = soup.h1.get_text().strip()

        # Extract Meta Description
        snippet = ""
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_desc and meta_desc.get("content"):
            snippet = meta_desc["content"].strip()

        # Remove script, style, nav, header, footer, form elements
        for element in soup(["script", "style", "nav", "header", "footer", "form", "aside", "noscript"]):
            element.decompose()

        # Extract Main Body Text
        text = soup.get_text(separator=" ")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = " ".join(chunk for chunk in chunks if chunk)

        if not snippet and clean_text:
            snippet = clean_text[:200] + "..." if len(clean_text) > 200 else clean_text

        # Extract Outbound Links
        outbound_links: List[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            norm = UrlFrontier.normalize_url(href, base_url=page_url)
            if norm and norm not in outbound_links:
                outbound_links.append(norm)

        # Content hash for duplicate text detection
        content_hash = hashlib.md5(clean_text.encode("utf-8")).hexdigest()

        return {
            "title": title[:500] if title else page_url,
            "snippet": snippet[:1000] if snippet else "",
            "content_text": clean_text,
            "word_count": len(clean_text.split()),
            "outbound_links": outbound_links[:100],  # Limit max 100 links per page
            "content_hash": content_hash
        }


class WebCrawlerService:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self._task: Optional[asyncio.Task] = None
        self.domain_last_crawled: Dict[str, float] = {}
        self.politeness_delay = 0.8  # seconds between requests to same domain
        self.user_agent = "FIND-Engine-Crawler/1.0 (+https://find-engine.private/bot)"

    async def get_stats(self) -> Dict[str, Any]:
        sm = get_sessionmaker()
        async with sm() as db:
            crawled_count = (await db.execute(select(func.count(CrawledDocument.id)))).scalar() or 0
            queued_count = (await db.execute(select(func.count(CrawlQueue.id)).where(CrawlQueue.status == "pending"))).scalar() or 0
            failed_count = (await db.execute(select(func.count(CrawlQueue.id)).where(CrawlQueue.status == "failed"))).scalar() or 0
            
            # Aggregate stats entry
            stat_res = await db.execute(select(CrawlStat).limit(1))
            stat_obj = stat_res.scalars().first()

            return {
                "status": "running" if self.is_running else ("paused" if self.is_paused else "idle"),
                "pages_crawled": crawled_count,
                "pages_queued": queued_count,
                "pages_failed": failed_count,
                "pages_target": stat_obj.pages_target if stat_obj else 100,
                "current_url": stat_obj.current_url if stat_obj else "",
                "preset_packs": list(PRESET_SEED_PACKS.keys())
            }

    async def add_seeds(self, seed_urls: List[str], reset_queue: bool = False):
        sm = get_sessionmaker()
        async with sm() as db:
            if reset_queue:
                await db.execute(delete(CrawlQueue))
                await db.commit()

            added_count = 0
            for raw_url in seed_urls:
                norm = UrlFrontier.normalize_url(raw_url)
                if not norm:
                    continue
                url_hash = UrlFrontier.hash_url(norm)
                domain = UrlFrontier.extract_domain(norm)

                # Check if already crawled or queued
                existing_doc = (await db.execute(select(CrawledDocument.id).where(CrawledDocument.url_hash == url_hash))).scalar()
                existing_queue = (await db.execute(select(CrawlQueue.id).where(CrawlQueue.url_hash == url_hash))).scalar()

                if not existing_doc and not existing_queue:
                    q_item = CrawlQueue(
                        url=norm,
                        url_hash=url_hash,
                        domain=domain,
                        depth=0,
                        status="pending"
                    )
                    db.add(q_item)
                    added_count += 1
            
            await db.commit()
            logger.info(f"Added {added_count} seed URLs to crawl queue.")
            return added_count

    async def start_crawl(self, seed_urls: Optional[List[str]] = None, target_pages: int = 100, depth_limit: int = 2):
        if self.is_running:
            return {"status": "already_running"}

        # Add seed URLs if provided
        if seed_urls and len(seed_urls) > 0:
            await self.add_seeds(seed_urls, reset_queue=False)
        else:
            # Check if queue has pending URLs, if empty seed with defaults
            sm = get_sessionmaker()
            async with sm() as db:
                pending_count = (await db.execute(select(func.count(CrawlQueue.id)).where(CrawlQueue.status == "pending"))).scalar() or 0
                if pending_count == 0:
                    default_seeds = PRESET_SEED_PACKS["documentation"] + PRESET_SEED_PACKS["wikipedia"]
                    await self.add_seeds(default_seeds, reset_queue=False)

        # Update CrawlStat
        sm = get_sessionmaker()
        async with sm() as db:
            stat_res = await db.execute(select(CrawlStat).limit(1))
            stat_obj = stat_res.scalars().first()
            if not stat_obj:
                stat_obj = CrawlStat(status="running", pages_target=target_pages, started_at=datetime.now(timezone.utc))
                db.add(stat_obj)
            else:
                stat_obj.status = "running"
                stat_obj.pages_target = target_pages
                stat_obj.updated_at = datetime.now(timezone.utc)
            await db.commit()

        self.is_running = True
        self.is_paused = False
        self._task = asyncio.create_task(self._crawl_loop(target_pages, depth_limit))
        return {"status": "started", "target_pages": target_pages}

    async def stop_crawl(self):
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
        
        sm = get_sessionmaker()
        async with sm() as db:
            stat_res = await db.execute(select(CrawlStat).limit(1))
            stat_obj = stat_res.scalars().first()
            if stat_obj:
                stat_obj.status = "idle"
                stat_obj.updated_at = datetime.now(timezone.utc)
                await db.commit()
        
        return {"status": "stopped"}

    async def _crawl_loop(self, target_pages: int, depth_limit: int):
        logger.info(f"Crawler background worker started. Target: {target_pages} pages.")
        
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=10.0,
            follow_redirects=True
        ) as client:
            while self.is_running:
                try:
                    # Fetch next pending URL from queue
                    sm = get_sessionmaker()
                    async with sm() as db:
                        crawled_count = (await db.execute(select(func.count(CrawledDocument.id)))).scalar() or 0
                        if crawled_count >= target_pages:
                            logger.info(f"Crawl target of {target_pages} pages reached!")
                            self.is_running = False
                            break

                        item_res = await db.execute(
                            select(CrawlQueue)
                            .where(CrawlQueue.status == "pending")
                            .order_by(CrawlQueue.depth.asc(), CrawlQueue.id.asc())
                            .limit(1)
                        )
                        queue_item = item_res.scalars().first()

                        if not queue_item:
                            logger.info("No more pending URLs in queue. Crawl complete.")
                            self.is_running = False
                            break

                        # Mark queue item as crawling
                        queue_item.status = "crawling"
                        await db.commit()

                        url = queue_item.url
                        domain = queue_item.domain
                        depth = queue_item.depth

                        # Update current URL in CrawlStat
                        stat_res = await db.execute(select(CrawlStat).limit(1))
                        stat_obj = stat_res.scalars().first()
                        if stat_obj:
                            stat_obj.current_url = url
                            await db.commit()

                    # Domain politeness delay
                    now = asyncio.get_event_loop().time()
                    last_time = self.domain_last_crawled.get(domain, 0.0)
                    elapsed = now - last_time
                    if elapsed < self.politeness_delay:
                        await asyncio.sleep(self.politeness_delay - elapsed)
                    self.domain_last_crawled[domain] = asyncio.get_event_loop().time()

                    # Download Page
                    logger.debug(f"Fetching URL: {url} (Depth: {depth})")
                    resp = await client.get(url)

                    # Verify HTML Content Type
                    content_type = resp.headers.get("content-type", "").lower()
                    if "text/html" not in content_type and "application/xhtml" not in content_type:
                        async with sm() as db:
                            q_ref = await db.merge(queue_item)
                            q_ref.status = "failed"
                            q_ref.error_msg = f"Non-HTML content type: {content_type}"
                            await db.commit()
                        continue

                    # Extract Content
                    extracted = ContentExtractor.extract(resp.text, url)
                    url_hash = UrlFrontier.hash_url(url)

                    async with sm() as db:
                        # Save Crawled Document
                        doc = CrawledDocument(
                            url=url,
                            url_hash=url_hash,
                            domain=domain,
                            title=extracted["title"],
                            snippet=extracted["snippet"],
                            content_text=extracted["content_text"],
                            word_count=extracted["word_count"],
                            depth=depth,
                            http_status=resp.status_code,
                            content_hash=extracted["content_hash"]
                        )
                        db.add(doc)

                        # Mark queue item completed
                        q_ref = await db.merge(queue_item)
                        q_ref.status = "completed"

                        # Discover & Queue Outbound Links if depth < limit
                        if depth < depth_limit:
                            new_links_count = 0
                            for link in extracted["outbound_links"]:
                                link_hash = UrlFrontier.hash_url(link)
                                link_domain = UrlFrontier.extract_domain(link)

                                # Check if already in doc or queue
                                doc_exists = (await db.execute(select(CrawledDocument.id).where(CrawledDocument.url_hash == link_hash))).scalar()
                                queue_exists = (await db.execute(select(CrawlQueue.id).where(CrawlQueue.url_hash == link_hash))).scalar()

                                if not doc_exists and not queue_exists:
                                    new_q = CrawlQueue(
                                        url=link,
                                        url_hash=link_hash,
                                        domain=link_domain,
                                        depth=depth + 1,
                                        status="pending"
                                    )
                                    db.add(new_q)
                                    new_links_count += 1
                                    if new_links_count >= 20:  # Max 20 new links queued per page
                                        break

                        await db.commit()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Error crawling URL: {e}")
                    try:
                        async with sm() as db:
                            if 'queue_item' in locals() and queue_item:
                                q_ref = await db.merge(queue_item)
                                q_ref.status = "failed"
                                q_ref.error_msg = str(e)[:450]
                                await db.commit()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)

        self.is_running = False
        logger.info("Crawler background worker finished.")

crawler_service = WebCrawlerService()
