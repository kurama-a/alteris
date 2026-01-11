"""
Module d'optimisation mémoire et performance pour le backend Alteris.
Gestion de la pagination, streaming, pooling et monitoring.
"""
import os
import gc
import sys
import asyncio
import logging
from typing import Any, AsyncGenerator, Optional, TypeVar, Generic, List
from dataclasses import dataclass
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger("performance")

T = TypeVar("T")


# =====================
# Configuration
# =====================

# MongoDB Connection Pool
MONGO_MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
MONGO_MAX_IDLE_TIME_MS = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", "30000"))  # 30 secondes
MONGO_WAIT_QUEUE_TIMEOUT_MS = int(os.getenv("MONGO_WAIT_QUEUE_TIMEOUT_MS", "10000"))  # 10 secondes
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))  # 5 secondes

# Pagination
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))

# Memory Management
MEMORY_THRESHOLD_MB = int(os.getenv("MEMORY_THRESHOLD_MB", "500"))
GC_COLLECTION_INTERVAL = int(os.getenv("GC_COLLECTION_INTERVAL", "300"))  # 5 minutes


# =====================
# Pagination optimisée
# =====================

@dataclass
class PaginatedResult(Generic[T]):
    """Résultat paginé standard."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResult[T]":
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous
            }
        }


async def paginate_cursor(
    collection,
    query: dict = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: list = None,
    projection: dict = None
) -> PaginatedResult:
    """
    Pagination optimisée pour les curseurs MongoDB.
    Utilise skip/limit avec comptage séparé pour de meilleures performances.
    """
    query = query or {}
    page_size = min(page_size, MAX_PAGE_SIZE)
    page = max(1, page)
    skip = (page - 1) * page_size
    
    # Exécuter le comptage et la requête en parallèle
    count_future = collection.count_documents(query)
    
    cursor = collection.find(query, projection)
    if sort:
        cursor = cursor.sort(sort)
    cursor = cursor.skip(skip).limit(page_size)
    
    # Attendre les deux résultats
    total, items = await asyncio.gather(
        count_future,
        cursor.to_list(length=page_size)
    )
    
    return PaginatedResult.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


async def cursor_pagination(
    collection,
    query: dict = None,
    cursor_field: str = "_id",
    cursor_value: Any = None,
    limit: int = DEFAULT_PAGE_SIZE,
    sort_direction: int = -1,
    projection: dict = None
) -> tuple[List[dict], Optional[Any]]:
    """
    Pagination par curseur (plus performante pour de grands datasets).
    Retourne (items, next_cursor).
    """
    query = query or {}
    limit = min(limit, MAX_PAGE_SIZE)
    
    if cursor_value:
        if sort_direction == -1:
            query[cursor_field] = {"$lt": cursor_value}
        else:
            query[cursor_field] = {"$gt": cursor_value}
    
    cursor = collection.find(query, projection)
    cursor = cursor.sort(cursor_field, sort_direction).limit(limit + 1)
    
    items = await cursor.to_list(length=limit + 1)
    
    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        next_cursor = items[-1][cursor_field] if items else None
    
    return items, next_cursor


# =====================
# Streaming pour grandes quantités de données
# =====================

async def stream_documents(
    collection,
    query: dict = None,
    batch_size: int = 100,
    projection: dict = None
) -> AsyncGenerator[dict, None]:
    """
    Générateur asynchrone pour streamer les documents.
    Utilise le batch_size pour optimiser la mémoire.
    """
    query = query or {}
    
    cursor = collection.find(query, projection).batch_size(batch_size)
    
    async for document in cursor:
        yield document


async def process_in_batches(
    collection,
    query: dict,
    processor: callable,
    batch_size: int = 100
) -> int:
    """
    Traite les documents par lots pour éviter la surcharge mémoire.
    Retourne le nombre total de documents traités.
    """
    processed = 0
    batch = []
    
    async for doc in stream_documents(collection, query, batch_size):
        batch.append(doc)
        
        if len(batch) >= batch_size:
            await processor(batch)
            processed += len(batch)
            batch = []
    
    # Traiter le dernier lot
    if batch:
        await processor(batch)
        processed += len(batch)
    
    return processed


# =====================
# Pool de connexions MongoDB optimisé
# =====================

_optimized_client: Optional[AsyncIOMotorClient] = None
_optimized_db: Optional[AsyncIOMotorDatabase] = None


def create_optimized_client(mongo_uri: str) -> AsyncIOMotorClient:
    """
    Crée un client MongoDB avec des paramètres de pool optimisés.
    """
    return AsyncIOMotorClient(
        mongo_uri,
        # Pool de connexions
        minPoolSize=MONGO_MIN_POOL_SIZE,
        maxPoolSize=MONGO_MAX_POOL_SIZE,
        maxIdleTimeMS=MONGO_MAX_IDLE_TIME_MS,
        waitQueueTimeoutMS=MONGO_WAIT_QUEUE_TIMEOUT_MS,
        
        # Timeouts
        serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
        connectTimeoutMS=5000,
        socketTimeoutMS=30000,
        
        # Performance
        retryWrites=True,
        retryReads=True,
        
        # Compression
        compressors=["zstd", "snappy", "zlib"],
    )


async def get_optimized_db(
    mongo_uri: str,
    db_name: str
) -> AsyncIOMotorDatabase:
    """
    Retourne une instance de base de données avec pool optimisé.
    """
    global _optimized_client, _optimized_db
    
    if _optimized_client is None:
        _optimized_client = create_optimized_client(mongo_uri)
        _optimized_db = _optimized_client[db_name]
    
    return _optimized_db


async def close_optimized_client():
    """Ferme le client optimisé proprement."""
    global _optimized_client, _optimized_db
    
    if _optimized_client:
        _optimized_client.close()
        _optimized_client = None
        _optimized_db = None


# =====================
# Monitoring mémoire
# =====================

@dataclass
class MemoryStats:
    """Statistiques mémoire du processus."""
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Pourcentage de la RAM totale
    gc_counts: tuple
    objects_count: int


def get_memory_stats() -> MemoryStats:
    """
    Retourne les statistiques mémoire actuelles.
    """
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()
        
        return MemoryStats(
            rss_mb=mem_info.rss / 1024 / 1024,
            vms_mb=mem_info.vms / 1024 / 1024,
            percent=mem_percent,
            gc_counts=gc.get_count(),
            objects_count=len(gc.get_objects())
        )
    except ImportError:
        # psutil non disponible
        return MemoryStats(
            rss_mb=0,
            vms_mb=0,
            percent=0,
            gc_counts=gc.get_count(),
            objects_count=len(gc.get_objects())
        )


def check_memory_threshold() -> tuple[bool, float]:
    """
    Vérifie si la mémoire dépasse le seuil configuré.
    Retourne (is_exceeded, current_mb).
    """
    stats = get_memory_stats()
    return stats.rss_mb > MEMORY_THRESHOLD_MB, stats.rss_mb


async def memory_monitor_task(interval: int = GC_COLLECTION_INTERVAL):
    """
    Tâche de fond pour surveiller la mémoire et déclencher le GC si nécessaire.
    """
    while True:
        try:
            await asyncio.sleep(interval)
            
            exceeded, current_mb = check_memory_threshold()
            
            if exceeded:
                logger.warning(f"Mémoire élevée: {current_mb:.1f}MB (seuil: {MEMORY_THRESHOLD_MB}MB)")
                gc.collect()
                
                # Vérifier à nouveau après GC
                _, new_mb = check_memory_threshold()
                logger.info(f"Après GC: {new_mb:.1f}MB (libéré: {current_mb - new_mb:.1f}MB)")
            else:
                logger.debug(f"Mémoire: {current_mb:.1f}MB")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Erreur monitoring mémoire: {e}")


# =====================
# Optimisation des requêtes
# =====================

class QueryOptimizer:
    """
    Utilitaires pour optimiser les requêtes MongoDB.
    """
    
    @staticmethod
    def build_text_search_query(search_term: str, fields: List[str]) -> dict:
        """
        Construit une requête de recherche textuelle optimisée.
        """
        if not search_term:
            return {}
        
        # Échapper les caractères spéciaux regex
        import re
        escaped = re.escape(search_term)
        regex = {"$regex": escaped, "$options": "i"}
        
        if len(fields) == 1:
            return {fields[0]: regex}
        
        return {"$or": [{field: regex} for field in fields]}
    
    @staticmethod
    def build_date_range_query(
        field: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Construit une requête de plage de dates.
        """
        if not start_date and not end_date:
            return {}
        
        query = {field: {}}
        
        if start_date:
            query[field]["$gte"] = start_date
        if end_date:
            query[field]["$lte"] = end_date
        
        return query
    
    @staticmethod
    def projection_for_list(include_fields: List[str]) -> dict:
        """
        Crée une projection pour les listes (exclut les champs volumineux).
        """
        return {field: 1 for field in include_fields}
    
    @staticmethod
    def ensure_indexes(collection, indexes: List[tuple]):
        """
        Assure que les index nécessaires existent.
        À appeler au démarrage de l'application.
        
        Usage:
            await QueryOptimizer.ensure_indexes(collection, [
                ("email", 1),  # Index simple
                ([("nom", 1), ("prenom", 1)], {"name": "nom_prenom_idx"})  # Index composé
            ])
        """
        async def create_indexes():
            for index_spec in indexes:
                if isinstance(index_spec, tuple) and len(index_spec) == 2:
                    if isinstance(index_spec[0], list):
                        # Index composé avec options
                        await collection.create_index(index_spec[0], **index_spec[1])
                    else:
                        # Index simple
                        await collection.create_index([index_spec])
                else:
                    await collection.create_index([index_spec])
        
        return create_indexes()


# =====================
# Utilitaires de performance
# =====================

async def run_with_timeout(coro, timeout_seconds: float = 30.0):
    """
    Exécute une coroutine avec un timeout.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Timeout atteint après {timeout_seconds}s")
        raise


class PerformanceMetrics:
    """
    Collecteur de métriques de performance.
    """
    
    def __init__(self):
        self._request_times: List[float] = []
        self._max_samples = 1000
    
    def record_request_time(self, duration_ms: float):
        """Enregistre le temps d'une requête."""
        self._request_times.append(duration_ms)
        
        # Limiter la taille
        if len(self._request_times) > self._max_samples:
            self._request_times = self._request_times[-self._max_samples:]
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de performance."""
        if not self._request_times:
            return {"message": "Aucune donnée"}
        
        sorted_times = sorted(self._request_times)
        n = len(sorted_times)
        
        return {
            "count": n,
            "avg_ms": sum(sorted_times) / n,
            "min_ms": sorted_times[0],
            "max_ms": sorted_times[-1],
            "p50_ms": sorted_times[n // 2],
            "p95_ms": sorted_times[int(n * 0.95)] if n >= 20 else None,
            "p99_ms": sorted_times[int(n * 0.99)] if n >= 100 else None,
        }


# Instance globale des métriques
performance_metrics = PerformanceMetrics()
