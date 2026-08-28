import os
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete

from database import init_db, get_db, User, SearchHistory, Bookmark
from cache import cache_manager
from auth import hash_password, verify_password, create_access_token, get_current_user
from orchestrator import SearchOrchestrator

# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class BookmarkCreate(BaseModel):
    title: str
    url: str
    domain: str
    snippet: Optional[str] = ""
    source: str
    raw_score: Optional[float] = 0.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database Tables
    await init_db()
    
    # Initialize Redis Connection
    await cache_manager.connect()

    # Seed Default Admin Account if users table is empty
    async for db in get_db():
        result = await db.execute(select(User).limit(1))
        existing_user = result.scalars().first()
        if not existing_user:
            default_user = os.getenv("ADMIN_USERNAME", "admin")
            default_pass = os.getenv("ADMIN_PASSWORD", "admin123")
            admin = User(
                username=default_user,
                password_hash=hash_password(default_pass),
                full_name="Private Infrastructure Admin",
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print(f"[INIT] Created default private user: '{default_user}'")
        break
        
    yield
    
    # Cleanup Redis
    await cache_manager.close()

app = FastAPI(
    title="FIND-engine Private Infrastructure API",
    description="Encrypted Metasearch Engine with PostgreSQL persistence, Redis caching, and JWT Authentication.",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = SearchOrchestrator()

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    redis_status = await cache_manager.is_healthy()
    db_status = True
    try:
        await db.execute(select(User).limit(1))
    except Exception:
        db_status = False

    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "cache_redis": "active" if redis_status else "offline",
        "infrastructure": "Private VPN / TLS Network"
    }

# Authentication Endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == credentials.username.strip()))
    user = result.scalars().first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at.isoformat()
    }

# Protected Search Endpoint
@app.get("/api/search")
async def search(
    q: str = Query(..., description="The search query string"),
    category: Optional[str] = Query(None, description="Optional category bias"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    if not q.strip():
        return {"results": [], "is_cached": False}

    cat = category or "all"
    
    # 1. Check Redis Cache
    cached_results = await cache_manager.get_search(q, cat)
    if cached_results is not None:
        # Record search history asynchronously in DB
        history_entry = SearchHistory(
            user_id=current_user.id,
            query=q.strip(),
            category=cat,
            result_count=len(cached_results)
        )
        db.add(history_entry)
        await db.commit()
        return {"results": cached_results, "is_cached": True}

    # 2. Cache Miss: Execute Live Search Orchestrator
    results = await orchestrator.search(q, category=cat)

    # 3. Save to Redis Cache (10 mins)
    await cache_manager.set_search(q, cat, results, ttl_seconds=600)

    # 4. Save to PostgreSQL Search History
    history_entry = SearchHistory(
        user_id=current_user.id,
        query=q.strip(),
        category=cat,
        result_count=len(results)
    )
    db.add(history_entry)
    await db.commit()

    return {"results": results, "is_cached": False}

# User History & Bookmarks Endpoints
@app.get("/api/history")
async def get_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(desc(SearchHistory.created_at))
        .limit(30)
    )
    result = await db.execute(stmt)
    history = result.scalars().all()
    return [
        {
            "id": item.id,
            "query": item.query,
            "category": item.category,
            "result_count": item.result_count,
            "created_at": item.created_at.isoformat()
        }
        for item in history
    ]

@app.get("/api/bookmarks")
async def get_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .order_by(desc(Bookmark.created_at))
    )
    result = await db.execute(stmt)
    bookmarks = result.scalars().all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "url": b.url,
            "domain": b.domain,
            "snippet": b.snippet,
            "source": b.source,
            "raw_score": b.raw_score,
            "created_at": b.created_at.isoformat()
        }
        for b in bookmarks
    ]

@app.post("/api/bookmarks")
async def create_bookmark(
    bookmark: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if URL already bookmarked
    stmt = select(Bookmark).where(Bookmark.user_id == current_user.id, Bookmark.url == bookmark.url)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        return {"status": "exists", "id": existing.id}

    new_bm = Bookmark(
        user_id=current_user.id,
        title=bookmark.title,
        url=bookmark.url,
        domain=bookmark.domain,
        snippet=bookmark.snippet,
        source=bookmark.source,
        raw_score=bookmark.raw_score
    )
    db.add(new_bm)
    await db.commit()
    await db.refresh(new_bm)
    return {"status": "created", "id": new_bm.id}

@app.delete("/api/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = delete(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == current_user.id)
    await db.execute(stmt)
    await db.commit()
    return {"status": "deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
