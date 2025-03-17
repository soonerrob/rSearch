"""Cache module for storing AI responses."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class Cache:
    """Simple in-memory cache with expiration."""
    
    def __init__(self):
        """Initialize cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Dict]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if datetime.utcnow() > entry['expires']:
            del self._cache[key]
            return None
            
        return entry['value']
    
    async def set(self, key: str, value: Dict, expire: int = 3600) -> None:
        """Set value in cache with expiration in seconds."""
        self._cache[key] = {
            'value': value,
            'expires': datetime.utcnow() + timedelta(seconds=expire)
        }
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
    
    async def clear(self) -> None:
        """Clear all values from cache."""
        self._cache.clear()

# Global cache instance
_cache = Cache()

def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache 