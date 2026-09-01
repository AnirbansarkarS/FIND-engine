import os
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import String, Integer, DateTime, Text, Float, ForeignKey, Boolean, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

_engine = None

def _get_db_url() -> str:
    """
    Returns the database URL. Defaults to SQLite for zero-config local dev.
    Set DATABASE_URL env var to a postgresql+asyncpg:// URL for production.
    """
    url = os.getenv("DATABASE_URL", "")
    if url:
        # Support plain postgres:// URLs by converting to asyncpg driver
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    # Local default: SQLite in the backend directory
    db_path = os.path.join(os.path.dirname(__file__), "findengine.db")
    return f"sqlite+aiosqlite:///{db_path}"

def get_engine():
    global _engine
    if _engine is None:
        db_url = _get_db_url()
        if "sqlite" in db_url:
            _engine = create_async_engine(
                db_url,
                echo=False,
                connect_args={"check_same_thread": False},
            )
        else:
            _engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
            )
    return _engine

def get_sessionmaker():
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    history: Mapped[list["SearchHistory"]] = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    bookmarks: Mapped[list["Bookmark"]] = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="all")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="history")

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="bookmarks")


class CrawledDocument(Base):
    __tablename__ = "crawled_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    snippet: Mapped[str] = mapped_column(Text, nullable=True, default="")
    content_text: Mapped[str] = mapped_column(Text, nullable=True, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    http_status: Mapped[int] = mapped_column(Integer, default=200)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class CrawlQueue(Base):
    __tablename__ = "crawl_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, crawling, completed, failed
    error_msg: Mapped[str] = mapped_column(String(500), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class CrawlStat(Base):
    __tablename__ = "crawl_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="idle")  # idle, running, paused, completed
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    pages_queued: Mapped[int] = mapped_column(Integer, default=0)
    pages_target: Mapped[int] = mapped_column(Integer, default=100)
    active_workers: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    current_url: Mapped[str] = mapped_column(String(2048), nullable=True, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db():
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Initialize SQLite FTS5 table if using SQLite
        if "sqlite" in str(eng.url):
            try:
                from sqlalchemy import text
                await conn.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS crawled_fts USING fts5(
                        title,
                        snippet,
                        content_text,
                        domain,
                        url,
                        content='crawled_documents',
                        content_rowid='id'
                    );
                """))
                
                # Triggers to keep FTS index updated with main table
                await conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS crawled_ai AFTER INSERT ON crawled_documents BEGIN
                        INSERT INTO crawled_fts(rowid, title, snippet, content_text, domain, url)
                        VALUES (new.id, new.title, new.snippet, new.content_text, new.domain, new.url);
                    END;
                """))
                await conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS crawled_ad AFTER DELETE ON crawled_documents BEGIN
                        INSERT INTO crawled_fts(crawled_fts, rowid, title, snippet, content_text, domain, url)
                        VALUES('delete', old.id, old.title, old.snippet, old.content_text, old.domain, old.url);
                    END;
                """))
                await conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS crawled_au AFTER UPDATE ON crawled_documents BEGIN
                        INSERT INTO crawled_fts(crawled_fts, rowid, title, snippet, content_text, domain, url)
                        VALUES('delete', old.id, old.title, old.snippet, old.content_text, old.domain, old.url);
                        INSERT INTO crawled_fts(rowid, title, snippet, content_text, domain, url)
                        VALUES (new.id, new.title, new.snippet, new.content_text, new.domain, new.url);
                    END;
                """))
            except Exception as e:
                print(f"[INIT DB] FTS setup note: {e}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        finally:
            await session.close()

