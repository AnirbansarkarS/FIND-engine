import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
import dotenv

dotenv.load_dotenv()

# Set test database URL before database engine is initialized
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


import database
from database import init_db, get_db, get_engine, get_sessionmaker, Base, User, SearchHistory, Bookmark
from auth import hash_password, verify_password, create_access_token, decode_token
from main import app

async def run_tests():
    print("=== STARTING PRIVATE INFRASTRUCTURE INTEGRATION TESTS ===")
    
    # 1. Test Password Hashing & Verification
    plain = "admin123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed), "Password verification failed!"
    assert not verify_password("wrongpass", hashed), "Invalid password accepted!"
    print("[OK] Password hashing & verification passed.")

    # 2. Test JWT Token Generation & Decoding
    token = create_access_token({"sub": "admin"})
    payload = decode_token(token)
    assert payload.get("sub") == "admin", "JWT decoding failed!"
    print("[OK] JWT Token generation & validation passed.")

    # 3. Test Database Models & FastAPI Endpoints
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed Admin User
    sm = get_sessionmaker()
    async with sm() as session:
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            full_name="Admin Test User",
            is_active=True
        )
        session.add(admin)
        await session.commit()
    print("[OK] Database setup & user seeding passed.")


    # 4. Test API Endpoints using AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # A. Health Check
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        assert data["infrastructure"] == "Private VPN / TLS Network"
        print("[OK] Health check endpoint passed.")

        # B. Unauthenticated Search Access -> Should fail with 403/401
        res = await client.get("/api/search?q=python")
        assert res.status_code in (401, 403), f"Unauthenticated access permitted! Status: {res.status_code}"
        print("[OK] Unauthenticated route protection passed.")

        # C. Login Endpoint
        res = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert res.status_code == 200, f"Login failed: {res.text}"
        auth_data = res.json()
        assert "access_token" in auth_data, "No access token in login response"
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[OK] Authentication & JWT login passed.")

        # D. Get Me Profile Endpoint
        res = await client.get("/api/auth/me", headers=headers)
        assert res.status_code == 200, f"Get me failed: {res.text}"
        user_info = res.json()
        assert user_info["username"] == "admin"
        print("[OK] Authenticated user profile retrieval passed.")

        # E. Authenticated Search Endpoint
        res = await client.get("/api/search?q=Quantum", headers=headers)
        assert res.status_code == 200, f"Search failed: {res.text}"
        search_data = res.json()
        assert "results" in search_data, "Missing results in search response"
        assert len(search_data["results"]) > 0, "No results returned for search"
        print(f"[OK] Authenticated search passed. Retrieved {len(search_data['results'])} results.")

        # F. Search History Endpoint
        res = await client.get("/api/history", headers=headers)
        assert res.status_code == 200, f"History failed: {res.text}"
        history = res.json()
        assert len(history) >= 1, "Search history was not recorded"
        assert history[0]["query"] == "Quantum"
        print("[OK] Search history recording & retrieval in DB passed.")

        # G. Bookmark Creation Endpoint
        first_result = search_data["results"][0]
        bm_payload = {
            "title": first_result["title"],
            "url": first_result["url"],
            "domain": first_result["domain"],
            "snippet": first_result["snippet"],
            "source": first_result["source"],
            "raw_score": first_result.get("raw_score", 0.0)
        }
        res = await client.post("/api/bookmarks", json=bm_payload, headers=headers)
        assert res.status_code == 200, f"Bookmark creation failed: {res.text}"
        bm_res = res.json()
        assert bm_res["status"] == "created"
        bm_id = bm_res["id"]
        print("[OK] Bookmark creation in DB passed.")

        # H. Get Bookmarks Endpoint
        res = await client.get("/api/bookmarks", headers=headers)
        assert res.status_code == 200, f"Get bookmarks failed: {res.text}"
        bookmarks = res.json()
        assert len(bookmarks) == 1
        assert bookmarks[0]["url"] == first_result["url"]
        print("[OK] Bookmark retrieval passed.")

        # I. Delete Bookmark Endpoint
        res = await client.delete(f"/api/bookmarks/{bm_id}", headers=headers)
        assert res.status_code == 200
        res = await client.get("/api/bookmarks", headers=headers)
        assert len(res.json()) == 0
        print("[OK] Bookmark deletion passed.")

    print("\n=== ALL PRIVATE INFRASTRUCTURE INTEGRATION TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
