import os
import json
import logging
from typing import Optional, List, Dict, Any
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger("findengine.cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisCache:
    def __init__(self):
        self.redis: Any = None
        self._connected = False

    async def connect(self):
        if aioredis is None:
            logger.warning("redis library not installed. Running without Redis cache.")
            self._connected = False
            return
        try:
            self.redis = aioredis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            await self.redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache successfully.")
        except Exception as e:
            logger.warning(f"Redis cache connection unavailable: {e}. Running without Redis cache.")
            self._connected = False


    async def close(self):
        if self.redis and self._connected:
            await self.redis.close()

    def _make_key(self, query: str, category: str) -> str:
        clean_q = query.strip().lower()
        cat = (category or "all").strip().lower()
        return f"search_cache:{cat}:{clean_q}"

    async def get_search(self, query: str, category: str) -> Optional[List[Dict[str, Any]]]:
        if not self._connected or not self.redis:
            return None
        try:
            key = self._make_key(query, category)
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.info(f"Redis cache hit for query: '{query}' [category: {category}]")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")
        return None

    async def set_search(self, query: str, category: str, results: List[Dict[str, Any]], ttl_seconds: int = 600):
        if not self._connected or not self.redis:
            return
        try:
            key = self._make_key(query, category)
            await self.redis.set(key, json.dumps(results), ex=ttl_seconds)
            logger.info(f"Cached search results in Redis for '{query}' (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.warning(f"Failed to write to Redis cache: {e}")

    async def is_healthy(self) -> bool:
        if not self._connected or not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False

cache_manager = RedisCache()
