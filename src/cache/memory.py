import time
from typing import Any, Optional, Dict
from src.cache.interface import CacheInterface
import structlog

logger = structlog.get_logger()


class MemoryCache(CacheInterface):
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        logger.debug("cache_hit", key=key)
        return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }
        logger.debug("cache_set", key=key, ttl=ttl)
    
    async def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_delete", key=key)
    
    async def clear(self) -> None:
        self._cache.clear()
        logger.info("cache_cleared")
