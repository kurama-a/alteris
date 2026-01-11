"""
Tests pour le module de cache.
"""
import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.cache import (
    LRUCache,
    CacheEntry,
    get_cache,
    cached,
    cache_response,
    generate_cache_key,
    get_cache_stats,
    QueryCache,
)


class TestCacheEntry:
    """Tests pour CacheEntry."""
    
    def test_cache_entry_not_expired(self):
        """Une entrée fraîche n'est pas expirée."""
        entry = CacheEntry(value="test", expires_at=time.time() + 100)
        assert not entry.is_expired
        assert entry.ttl_remaining > 0
    
    def test_cache_entry_expired(self):
        """Une entrée passée est expirée."""
        entry = CacheEntry(value="test", expires_at=time.time() - 1)
        assert entry.is_expired
        assert entry.ttl_remaining == 0


class TestLRUCache:
    """Tests pour le cache LRU."""
    
    @pytest.fixture
    def cache(self):
        return LRUCache(max_size=10, default_ttl=60)
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Set et get fonctionnent correctement."""
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache):
        """Get retourne None pour une clé manquante."""
        result = await cache.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_expiration(self):
        """Les entrées expirent après le TTL."""
        cache = LRUCache(max_size=10, default_ttl=1)
        
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        # Attendre l'expiration
        await asyncio.sleep(1.1)
        
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_custom_ttl(self, cache):
        """Le TTL personnalisé fonctionne."""
        await cache.set("key1", "value1", ttl=1)
        assert await cache.get("key1") == "value1"
        
        await asyncio.sleep(1.1)
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Les entrées les plus anciennes sont évincées."""
        cache = LRUCache(max_size=3, default_ttl=60)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Accéder à key1 pour le rendre récent
        await cache.get("key1")
        
        # Ajouter une nouvelle entrée (devrait évincer key2)
        await cache.set("key4", "value4")
        
        assert await cache.get("key1") == "value1"  # Toujours là (récent)
        assert await cache.get("key2") is None  # Évincé
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Delete supprime une entrée."""
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        result = await cache.delete("key1")
        assert result is True
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        """Delete retourne False pour une clé inexistante."""
        result = await cache.delete("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache):
        """Delete pattern supprime les entrées correspondantes."""
        await cache.set("user:1:name", "John")
        await cache.set("user:1:email", "john@example.com")
        await cache.set("user:2:name", "Jane")
        await cache.set("other:key", "value")
        
        deleted = await cache.delete_pattern("user:1:")
        assert deleted == 2
        
        assert await cache.get("user:1:name") is None
        assert await cache.get("user:1:email") is None
        assert await cache.get("user:2:name") == "Jane"
        assert await cache.get("other:key") == "value"
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Clear vide tout le cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Cleanup supprime les entrées expirées."""
        cache = LRUCache(max_size=10, default_ttl=1)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2", ttl=60)  # TTL plus long
        
        await asyncio.sleep(1.1)
        
        expired_count = await cache.cleanup_expired()
        assert expired_count == 1
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
    
    @pytest.mark.asyncio
    async def test_stats(self, cache):
        """Les statistiques sont correctement collectées."""
        await cache.set("key1", "value1")
        
        await cache.get("key1")  # Hit
        await cache.get("key1")  # Hit
        await cache.get("nonexistent")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate_percent"] == pytest.approx(66.67, rel=0.1)


class TestCacheDecorator:
    """Tests pour le décorateur @cached."""
    
    @pytest.mark.asyncio
    async def test_cached_decorator_caches_result(self):
        """Le décorateur cache le résultat."""
        call_count = 0
        
        @cached(ttl=60, prefix="test")
        async def expensive_operation(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Premier appel
        result1 = await expensive_operation(5)
        assert result1 == 10
        assert call_count == 1
        
        # Deuxième appel (depuis le cache)
        result2 = await expensive_operation(5)
        assert result2 == 10
        assert call_count == 1  # Pas d'appel supplémentaire
    
    @pytest.mark.asyncio
    async def test_cached_decorator_different_args(self):
        """Le cache différencie les arguments."""
        call_count = 0
        
        @cached(ttl=60, prefix="test2")
        async def multiply(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * y
        
        await multiply(2, 3)
        await multiply(2, 3)  # Cache hit
        await multiply(3, 4)  # Nouveaux args
        
        assert call_count == 2


class TestGenerateCacheKey:
    """Tests pour la génération de clés de cache."""
    
    def test_same_args_same_key(self):
        """Mêmes arguments = même clé."""
        key1 = generate_cache_key(1, 2, name="test")
        key2 = generate_cache_key(1, 2, name="test")
        assert key1 == key2
    
    def test_different_args_different_key(self):
        """Arguments différents = clés différentes."""
        key1 = generate_cache_key(1, 2)
        key2 = generate_cache_key(1, 3)
        assert key1 != key2
    
    def test_order_of_kwargs_doesnt_matter(self):
        """L'ordre des kwargs n'affecte pas la clé."""
        key1 = generate_cache_key(a=1, b=2)
        key2 = generate_cache_key(b=2, a=1)
        assert key1 == key2


class TestQueryCache:
    """Tests pour le cache de requêtes."""
    
    @pytest.mark.asyncio
    async def test_get_or_fetch_cache_miss(self):
        """get_or_fetch exécute la fonction si cache miss."""
        cache = QueryCache()
        
        fetch_called = False
        async def fetch():
            nonlocal fetch_called
            fetch_called = True
            return {"id": "1", "name": "Test"}
        
        result = await cache.get_or_fetch("users", "1", fetch, ttl=60)
        
        assert fetch_called
        assert result["id"] == "1"
    
    @pytest.mark.asyncio
    async def test_invalidate_document(self):
        """Invalidation d'un document spécifique."""
        cache = QueryCache()
        
        async def fetch():
            return {"id": "1"}
        
        await cache.get_or_fetch("users", "1", fetch, ttl=60)
        
        result = await cache.invalidate_document("users", "1")
        assert result is True