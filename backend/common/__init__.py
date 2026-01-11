"""
Module common - Fonctionnalités partagées pour le backend Alteris.

Modules disponibles:
- config: Configuration centralisée
- db: Connexion MongoDB
- app_factory: Création d'applications FastAPI
- security: Headers de sécurité, rate limiting, validation
- cache: Cache LRU en mémoire
- performance: Pagination, optimisation, métriques
- audit: Logging et traçabilité
- brute_force: Protection contre les attaques
- sanitization: Validation et nettoyage des entrées
- jwt_manager: Gestion avancée des tokens JWT
"""

from common.config import settings, get_settings
from common.db import connect_to_mongo, close_mongo_connection

__all__ = [
    "settings",
    "get_settings", 
    "connect_to_mongo",
    "close_mongo_connection",
]
