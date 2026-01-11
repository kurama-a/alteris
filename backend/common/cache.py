"""
Module de cache pour le backend Alteris.
Fournit une abstraction de cache avec support en mémoire et Redis.
"""
import os
import time
import json
import hashlib
import logging
from typing import Any, Optional, Callable, TypeVar, Generic
from functools import wraps
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio
from dataclasses import dataclass, field

logger = logging.getLogger("cache")

# =====================
# Configuration
# =====================

CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))  # 5 minutes
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # entrées max
REDIS_URL = os.getenv("REDIS_URL")  # Si configuré, utiliser Redis

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Représente une entrée de cache."""
    value: T
    expires_at: float
    created_at: float = field(default_factory=time.time)
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    @property
    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())


class LRUCache:
    """
    Cache LRU (Least Recently Used) thread-safe en mémoire.
    Éviction automatique des entrées les plus anciennes quand max_size atteint.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            
            if entry.is_expired:
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None
            
            # Mettre à jour l'ordre LRU
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats["hits"] += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stocke une valeur dans le cache."""
        if not CACHE_ENABLED:
            return
        
        ttl = ttl if ttl is not None else self.default_ttl
        
        async with self._lock:
            # Éviction si nécessaire
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + ttl
            )
            self._cache.move_to_end(key)
    
    async def delete(self, key: str) -> bool:
        """Supprime une entrée du cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Supprime toutes les entrées correspondant au pattern (prefix)."""
        async with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def clear(self) -> None:
        """Vide tout le cache."""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Nettoie les entrées expirées. Retourne le nombre d'entrées supprimées."""
        async with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expires_at <= now
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats["expirations"] += 1
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Retourne les statistiques du cache."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate_percent": round(hit_rate, 2)
        }


# Instance globale du cache
_cache_instance: Optional[LRUCache] = None


def get_cache() -> LRUCache:
    """Retourne l'instance globale du cache."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LRUCache(
            max_size=CACHE_MAX_SIZE,
            default_ttl=CACHE_DEFAULT_TTL
        )
    return _cache_instance


# =====================
# Décorateurs de cache
# =====================

def generate_cache_key(*args, **kwargs) -> str:
    """Génère une clé de cache unique basée sur les arguments."""
    # Convertir args et kwargs en string sérialisable
    key_data = {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = CACHE_DEFAULT_TTL,
    prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Décorateur pour mettre en cache le résultat d'une fonction async.
    
    Args:
        ttl: Durée de vie du cache en secondes
        prefix: Préfixe pour la clé de cache
        key_builder: Fonction optionnelle pour construire la clé
    
    Usage:
        @cached(ttl=300, prefix="user")
        async def get_user(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            cache = get_cache()
            
            # Construire la clé
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__name__}"
                arg_hash = generate_cache_key(*args, **kwargs)
                cache_key = f"{prefix}:{func_name}:{arg_hash}" if prefix else f"{func_name}:{arg_hash}"
            
            # Vérifier le cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Exécuter et cacher
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        # Ajouter des méthodes utilitaires
        async def invalidate(*args, **kwargs):
            """Invalide l'entrée de cache pour ces arguments."""
            cache = get_cache()
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__name__}"
                arg_hash = generate_cache_key(*args, **kwargs)
                cache_key = f"{prefix}:{func_name}:{arg_hash}" if prefix else f"{func_name}:{arg_hash}"
            await cache.delete(cache_key)
        
        async def invalidate_all():
            """Invalide toutes les entrées de cache pour cette fonction."""
            cache = get_cache()
            func_name = f"{func.__module__}.{func.__name__}"
            pattern = f"{prefix}:{func_name}:" if prefix else f"{func_name}:"
            await cache.delete_pattern(pattern)
        
        wrapper.invalidate = invalidate
        wrapper.invalidate_all = invalidate_all
        wrapper.cache_key_prefix = prefix
        
        return wrapper
    return decorator


def cache_response(ttl: int = 60, vary_on: Optional[list[str]] = None):
    """
    Décorateur pour cacher les réponses HTTP des endpoints FastAPI.
    
    Args:
        ttl: Durée de vie du cache en secondes
        vary_on: Liste de paramètres query/path qui font varier le cache
    
    Usage:
        @router.get("/users")
        @cache_response(ttl=300, vary_on=["page", "limit"])
        async def get_users(page: int = 1, limit: int = 10):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            cache = get_cache()
            
            # Construire la clé basée sur vary_on ou tous les kwargs
            func_name = f"{func.__module__}.{func.__name__}"
            
            if vary_on:
                key_kwargs = {k: kwargs.get(k) for k in vary_on if k in kwargs}
            else:
                key_kwargs = kwargs
            
            arg_hash = generate_cache_key(**key_kwargs)
            cache_key = f"response:{func_name}:{arg_hash}"
            
            # Vérifier le cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Exécuter et cacher
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# =====================
# Cache pour les requêtes MongoDB fréquentes
# =====================

class QueryCache:
    """
    Cache spécialisé pour les requêtes MongoDB fréquentes.
    Supporte l'invalidation par collection.
    """
    
    def __init__(self):
        self._cache = get_cache()
    
    async def get_or_fetch(
        self,
        collection_name: str,
        query_id: str,
        fetch_func: Callable,
        ttl: int = 300
    ) -> Any:
        """
        Récupère du cache ou exécute la fonction de fetch.
        """
        cache_key = f"db:{collection_name}:{query_id}"
        
        cached_value = await self._cache.get(cache_key)
        if cached_value is not None:
            return cached_value
        
        result = await fetch_func()
        if result is not None:
            await self._cache.set(cache_key, result, ttl)
        
        return result
    
    async def invalidate_collection(self, collection_name: str) -> int:
        """Invalide tout le cache pour une collection."""
        return await self._cache.delete_pattern(f"db:{collection_name}:")
    
    async def invalidate_document(self, collection_name: str, doc_id: str) -> bool:
        """Invalide le cache pour un document spécifique."""
        cache_key = f"db:{collection_name}:{doc_id}"
        return await self._cache.delete(cache_key)


# Instance globale du query cache
query_cache = QueryCache()


# =====================
# Tâches de maintenance du cache
# =====================

async def cache_cleanup_task(interval: int = 60):
    """
    Tâche de fond pour nettoyer périodiquement le cache.
    À lancer au démarrage de l'application.
    """
    cache = get_cache()
    while True:
        try:
            await asyncio.sleep(interval)
            expired_count = await cache.cleanup_expired()
            if expired_count > 0:
                logger.info(f"Cache cleanup: {expired_count} entrées expirées supprimées")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du cache: {e}")


# =====================
# API de statistiques
# =====================

def get_cache_stats() -> dict:
    """Retourne les statistiques du cache pour monitoring."""
    cache = get_cache()
    return cache.get_stats()
