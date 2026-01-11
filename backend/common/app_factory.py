import os
import asyncio
import time
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.db import connect_to_mongo, close_mongo_connection
from common.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
    get_cors_origins,
    RATE_LIMIT_ENABLED
)
from common.cache import get_cache, cache_cleanup_task, get_cache_stats
from common.performance import (
    get_memory_stats,
    memory_monitor_task,
    performance_metrics,
    close_optimized_client
)

logger = logging.getLogger("app")

# Configuration
ENABLE_SECURITY_MIDDLEWARE = os.getenv("ENABLE_SECURITY_MIDDLEWARE", "true").lower() == "true"
ENABLE_PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"


def create_app(service_name: str, api, prefix: str) -> FastAPI:
    """
    Crée une application FastAPI avec tous les middlewares de sécurité,
    cache et monitoring de performance intégrés.
    """
    app = FastAPI(
        title=f"API {service_name}",
        description=f"Documentation de l'API {service_name}",
        version="1.0.0",
        openapi_url=f"{prefix}/openapi.json",
        docs_url=f"{prefix}/docs",
        redoc_url=f"{prefix}/redoc"
    )

    # =====================
    # Middlewares de sécurité (ordre important: dernier ajouté = premier exécuté)
    # =====================
    
    # 1. CORS (doit être avant les autres middlewares)
    cors_origins = get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )
    
    if ENABLE_SECURITY_MIDDLEWARE:
        # 2. Headers de sécurité
        app.add_middleware(SecurityHeadersMiddleware)
        
        # 3. Validation des requêtes
        app.add_middleware(RequestValidationMiddleware)
        
        # 4. Rate limiting
        if RATE_LIMIT_ENABLED:
            app.add_middleware(RateLimitMiddleware)

    # =====================
    # Middleware de performance
    # =====================
    
    @app.middleware("http")
    async def track_request_time(request: Request, call_next):
        """Mesure le temps de traitement des requêtes."""
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        if ENABLE_PERFORMANCE_MONITORING:
            performance_metrics.record_request_time(duration_ms)
        
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response

    # =====================
    # Tâches de fond
    # =====================
    
    _background_tasks = []

    @app.on_event("startup")
    async def startup():
        """Initialisation au démarrage."""
        await connect_to_mongo()
        
        # Lancer les tâches de fond
        if ENABLE_PERFORMANCE_MONITORING:
            _background_tasks.append(
                asyncio.create_task(cache_cleanup_task(interval=60))
            )
            _background_tasks.append(
                asyncio.create_task(memory_monitor_task(interval=300))
            )
        
        logger.info(f"Service {service_name} démarré avec succès")

    @app.on_event("shutdown")
    async def shutdown():
        """Nettoyage à l'arrêt."""
        # Annuler les tâches de fond
        for task in _background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await close_mongo_connection()
        await close_optimized_client()
        
        logger.info(f"Service {service_name} arrêté proprement")

    # =====================
    # Routes système
    # =====================
    
    app.include_router(api, prefix=prefix)

    @app.get(f"{prefix}/health", tags=["System"])
    def health():
        """Vérification de santé du service."""
        return {"status": "ok", "service": service_name.lower()}

    @app.get(f"{prefix}/metrics", tags=["System"])
    async def metrics():
        """
        Métriques de performance et monitoring.
        Désactivé en production sans authentification appropriée.
        """
        if not ENABLE_PERFORMANCE_MONITORING:
            return JSONResponse(
                status_code=403,
                content={"detail": "Métriques désactivées"}
            )
        
        memory_stats = get_memory_stats()
        cache_stats = get_cache_stats()
        perf_stats = performance_metrics.get_stats()
        
        return {
            "service": service_name.lower(),
            "memory": {
                "rss_mb": round(memory_stats.rss_mb, 2),
                "gc_counts": memory_stats.gc_counts,
            },
            "cache": cache_stats,
            "performance": perf_stats,
        }

    @app.get(f"{prefix}/ready", tags=["System"])
    async def readiness():
        """Vérification de disponibilité (pour Kubernetes)."""
        # Vérifier la connexion DB
        try:
            from common.db import db
            await db.command("ping")
            db_status = "ok"
        except Exception:
            db_status = "error"
        
        status = "ok" if db_status == "ok" else "degraded"
        
        return {
            "status": status,
            "service": service_name.lower(),
            "checks": {
                "database": db_status
            }
        }

    return app
