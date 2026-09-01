import re
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database import CrawledDocument, get_engine
from providers.base import SearchResult

logger = logging.getLogger("findengine.index")

class SearchIndexEngine:
    """
    Search Index Engine for FIND-engine.
    Executes full-text queries against locally crawled pages using SQLite FTS5 
    (with BM25 ranking and snippet generation) or standard SQL fallback.
    """

    @staticmethod
    def _clean_query(query: str) -> str:
        """Sanitize query string for FTS syntax safety."""
        # Replace non-alphanumeric chars with spaces except quotes
        cleaned = re.sub(r'[^\w\s"]', ' ', query).strip()
        words = [w for w in cleaned.split() if len(w) > 0]
        if not words:
            return ""
        # Return boolean match query (word1 OR word2 or word1* word2*)
        return " OR ".join(f"{w}*" for w in words)

    async def search_index(
        self, 
        db: AsyncSession, 
        query: str, 
        limit: int = 30
    ) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        clean_q = query.strip()
        fts_q = self._clean_query(clean_q)
        results: List[SearchResult] = []

        engine = get_engine()
        is_sqlite = "sqlite" in str(engine.url)

        # 1. Try SQLite FTS5 Search with BM25 Scoring
        if is_sqlite and fts_q:
            try:
                fts_sql = text("""
                    SELECT 
                        d.id,
                        d.url,
                        d.domain,
                        d.title,
                        COALESCE(snippet(crawled_fts, 2, '<b>', '</b>', '...', 32), d.snippet) as highlight_snippet,
                        d.crawled_at,
                        bm25(crawled_fts, 5.0, 3.0, 1.0, 2.0, 1.0) as fts_rank
                    FROM crawled_fts f
                    JOIN crawled_documents d ON f.rowid = d.id
                    WHERE crawled_fts MATCH :query
                    ORDER BY fts_rank ASC
                    LIMIT :limit;
                """)
                res = await db.execute(fts_sql, {"query": fts_q, "limit": limit})
                rows = res.fetchall()

                for row in rows:
                    # bm25 rank in FTS5 returns negative/smaller value for better match
                    raw_score = round(max(0.5, 1.0 / (abs(row.fts_rank) + 0.1)), 4)
                    date_str = row.crawled_at.isoformat() if row.crawled_at else None
                    results.append(
                        SearchResult(
                            title=row.title or row.url,
                            url=row.url,
                            domain=row.domain,
                            snippet=row.highlight_snippet or "Crawled document match",
                            source="Local Crawler",
                            published_date=date_str,
                            raw_score=raw_score
                        )
                    )
                if results:
                    return results
            except Exception as e:
                logger.debug(f"FTS5 query fallback triggered: {e}")

        # 2. Fallback: Standard SQL LIKE search (PostgreSQL or SQLite fallback)
        query_words = [w.lower() for w in clean_q.split() if len(w) > 1]
        if not query_words:
            return []

        filters = []
        for word in query_words:
            pattern = f"%{word}%"
            filters.append(CrawledDocument.title.ilike(pattern))
            filters.append(CrawledDocument.content_text.ilike(pattern))
            filters.append(CrawledDocument.snippet.ilike(pattern))

        stmt = (
            select(CrawledDocument)
            .where(or_(*filters))
            .limit(limit)
        )
        res = await db.execute(stmt)
        docs = res.scalars().all()

        for doc in docs:
            # Simple keyword hit scoring
            title_hits = sum(1 for w in query_words if w in (doc.title or "").lower())
            body_hits = sum(1 for w in query_words if w in (doc.content_text or "").lower())
            score = round(min(1.0, (title_hits * 0.4 + body_hits * 0.1) / (len(query_words) * 0.4)), 4)

            # Basic snippet extraction around matching word
            snippet_text = doc.snippet or ""
            if not snippet_text and doc.content_text:
                first_word = query_words[0]
                idx = doc.content_text.lower().find(first_word)
                if idx != -1:
                    start = max(0, idx - 60)
                    end = min(len(doc.content_text), idx + 140)
                    snippet_text = ("..." if start > 0 else "") + doc.content_text[start:end] + "..."
                else:
                    snippet_text = doc.content_text[:200] + "..."

            results.append(
                SearchResult(
                    title=doc.title or doc.url,
                    url=doc.url,
                    domain=doc.domain,
                    snippet=snippet_text or "Crawled document match",
                    source="Local Crawler",
                    published_date=doc.crawled_at.isoformat() if doc.crawled_at else None,
                    raw_score=score
                )
            )

        # Sort descending by score
        results.sort(key=lambda x: x.raw_score or 0.0, reverse=True)
        return results

index_engine = SearchIndexEngine()
