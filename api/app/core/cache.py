"""Simple in-memory cache manager with TTL support."""
from cachetools import TTLCache
from app.core.config import settings


class CacheManager:
    def __init__(self):
        self._cache: TTLCache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl_seconds,
        )

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value) -> None:
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()

    def info(self) -> dict:
        return {
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "ttl_seconds": self._cache.ttl,
            "currsize": self._cache.currsize,
        }


cache_manager = CacheManager()
