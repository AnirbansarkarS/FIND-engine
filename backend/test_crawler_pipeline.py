import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

# Force SQLite in-memory for testing environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from database import init_db, get_db, CrawledDocument, CrawlQueue, User
from crawler import UrlFrontier, ContentExtractor, crawler_service, PRESET_SEED_PACKS
from index_engine import index_engine
from main import app
from auth import create_access_token

async def run_tests():
    print("=== STARTING CRAWLER & LOCAL INDEX PIPELINE INTEGRATION TESTS ===")

    # 1. Test URL Frontier & Normalization
    raw_url = "HTTPS://WWW.Example.com/Path/To/Page/?utm_source=test&gclid=123&q=python"
    norm_url = UrlFrontier.normalize_url(raw_url)
    assert norm_url == "https://example.com/Path/To/Page?q=python", f"Normalization failed: {norm_url}"

    domain = UrlFrontier.extract_domain(norm_url)
    assert domain == "example.com", f"Domain extraction failed: {domain}"
    print("[OK] URL Frontier normalization & domain extraction passed.")

    # 2. Test Content Extractor
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>FastAPI Web Framework</title>
        <meta name="description" content="FastAPI is a modern web framework for Python.">
      </head>
      <body>
        <nav><a href="/ignore-nav">Nav Link</a></nav>
        <h1>Welcome to FastAPI Documentation</h1>
        <p>FastAPI provides high performance and automatic interactive API documentation.</p>
        <a href="https://fastapi.tiangolo.com/tutorial/">Tutorial Guide</a>
        <script>console.log("script block");</script>
      </body>
    </html>
    """
    extracted = ContentExtractor.extract(sample_html, "https://fastapi.tiangolo.com/")
    assert extracted["title"] == "FastAPI Web Framework", f"Title extraction failed: {extracted['title']}"
    assert "modern web framework" in extracted["snippet"], f"Snippet extraction failed: {extracted['snippet']}"
    assert "Welcome to FastAPI" in extracted["content_text"]
    assert "https://fastapi.tiangolo.com/tutorial" in extracted["outbound_links"]
    print("[OK] HTML Content Extractor passed.")

    # 3. Test Database & FTS Index
    await init_db()
    async for db in get_db():
        # Seed test admin user for FastAPI auth dependency
        from auth import hash_password
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            full_name="Test Admin",
            is_active=True
        )
        db.add(admin)

        # Seed test documents
        doc1 = CrawledDocument(
            url="https://docs.python.org/3/tutorial/",
            url_hash=UrlFrontier.hash_url("https://docs.python.org/3/tutorial/"),
            domain="docs.python.org",
            title="The Python Tutorial — Python 3.12 documentation",
            snippet="Python is an easy to learn, powerful programming language with efficient high-level data structures.",
            content_text="Python is an easy to learn, powerful programming language with efficient data structures and object-oriented programming.",
            word_count=120,
            depth=0,
            http_status=200
        )

        doc2 = CrawledDocument(
            url="https://react.dev/",
            url_hash=UrlFrontier.hash_url("https://react.dev/"),
            domain="react.dev",
            title="React — The library for web and native user interfaces",
            snippet="React lets you build user interfaces out of individual pieces called components.",
            content_text="Build user interfaces out of components. Combine components into complex web applications.",
            word_count=85,
            depth=0,
            http_status=200
        )
        db.add(doc1)
        db.add(doc2)
        await db.commit()

        # Query Local Index Engine
        results = await index_engine.search_index(db, "Python tutorial")
        assert len(results) >= 1, "Local index search returned zero results for 'Python tutorial'"
        assert "python.org" in results[0].url.lower()
        assert results[0].source == "Local Crawler"
        print(f"[OK] Local Index Engine search query matched: '{results[0].title}'")

        # Test query for React
        react_res = await index_engine.search_index(db, "React components")
        assert len(react_res) >= 1
        assert "react.dev" in react_res[0].url
        print(f"[OK] Local Index Engine search query matched: '{react_res[0].title}'")
        break

    # 4. Test API Endpoints via AsyncClient
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Check crawler status
        res = await ac.get("/api/crawler/status", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "pages_crawled" in data
        print("[OK] /api/crawler/status endpoint passed.")

        # Test adding seed URLs
        res = await ac.post("/api/crawler/seeds", json=["https://example.org/test"], headers=headers)
        assert res.status_code == 200
        print("[OK] /api/crawler/seeds endpoint passed.")

        # Test listing crawled documents
        res = await ac.get("/api/crawler/documents", headers=headers)
        assert res.status_code == 200
        docs_list = res.json()
        assert len(docs_list) >= 2
        print(f"[OK] /api/crawler/documents returned {len(docs_list)} documents.")

        # Test searching with category="local" in main search endpoint
        res = await ac.get("/api/search?q=Python&category=local", headers=headers)
        assert res.status_code == 200
        search_data = res.json()
        assert len(search_data["results"]) >= 1
        assert search_data["results"][0]["source"] == "Local Crawler"
        print(f"[OK] /api/search?category=local returned offline local results.")

    print("\n=== ALL CRAWLER & INDEX PIPELINE TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
