"""
Configuration centralisée pour le backend Alteris.
Gestion des variables d'environnement avec validation.
"""
import os
from typing import Optional
from functools import lru_cache


class Settings:
    """
    Configuration de l'application.
    Toutes les valeurs sensibles doivent venir de variables d'environnement.
    """
    
    # =====================
    # Application
    # =====================
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # =====================
    # Base de données MongoDB
    # =====================
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "alternance_db")
    
    # Pool de connexions
    MONGO_MIN_POOL_SIZE: int = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
    MONGO_MAX_POOL_SIZE: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
    
    # =====================
    # Sécurité
    # =====================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    @property
    def jwt_secret_key(self) -> str:
        if self.SECRET_KEY:
            return self.SECRET_KEY
        if self.APP_ENV == "production":
            raise ValueError("SECRET_KEY doit être définie en production!")
        return "dev-only-secret-key-do-not-use-in-production"
    
    # JWT
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    
    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # =====================
    # Cache
    # =====================
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # =====================
    # Performance
    # =====================
    ENABLE_PERFORMANCE_MONITORING: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    MEMORY_THRESHOLD_MB: int = int(os.getenv("MEMORY_THRESHOLD_MB", "500"))
    
    # =====================
    # Pagination
    # =====================
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # =====================
    # Logging
    # =====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> list:
        """Valide la configuration."""
        errors = []
        if self.APP_ENV == "production":
            if not self.SECRET_KEY:
                errors.append("SECRET_KEY doit être définie en production")
            if self.ALLOWED_ORIGINS == "*":
                errors.append("ALLOWED_ORIGINS ne devrait pas être '*' en production")
        return errors
    
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
    
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """Retourne l'instance des settings."""
    return Settings()


# Instance globale pour rétrocompatibilité
settings = Settings()