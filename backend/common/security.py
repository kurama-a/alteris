"""
Module de sécurité centralisé pour le backend Alteris.
Gestion des headers de sécurité, rate limiting, validation et protection.
"""
import os
import re
import time
import secrets
import hashlib
import logging
from typing import Dict, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# =====================
# Configuration
# =====================

logger = logging.getLogger("security")

# Variables d'environnement pour la sécurité
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # requêtes par fenêtre
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # secondes
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
TRUSTED_PROXIES = os.getenv("TRUSTED_PROXIES", "").split(",")


# =====================
# Rate Limiter en mémoire (pour production, utiliser Redis)
# =====================

class InMemoryRateLimiter:
    """
    Rate limiter simple basé en mémoire.
    Pour la production, remplacer par Redis ou Memcached.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
    
    def _cleanup_old_entries(self):
        """Nettoie les entrées expirées pour économiser la mémoire."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff = now - self.window_seconds
        keys_to_delete = []
        
        for key, timestamps in self._requests.items():
            self._requests[key] = [ts for ts in timestamps if ts > cutoff]
            if not self._requests[key]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._requests[key]
        
        self._last_cleanup = now
    
    def is_rate_limited(self, identifier: str) -> tuple[bool, int]:
        """
        Vérifie si l'identifiant est rate limité.
        Retourne (is_limited, remaining_requests).
        """
        self._cleanup_old_entries()
        
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Filtrer les timestamps valides
        valid_requests = [ts for ts in self._requests[identifier] if ts > cutoff]
        self._requests[identifier] = valid_requests
        
        remaining = max(0, self.max_requests - len(valid_requests))
        
        if len(valid_requests) >= self.max_requests:
            return True, 0
        
        # Enregistrer cette requête
        self._requests[identifier].append(now)
        return False, remaining - 1
    
    def get_reset_time(self, identifier: str) -> int:
        """Retourne le temps restant avant reset en secondes."""
        if identifier not in self._requests or not self._requests[identifier]:
            return 0
        
        oldest = min(self._requests[identifier])
        reset_at = oldest + self.window_seconds
        return max(0, int(reset_at - time.time()))


# Instance globale du rate limiter
rate_limiter = InMemoryRateLimiter(
    max_requests=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW
)

# Rate limiter spécifique pour les endpoints sensibles (login, register)
auth_rate_limiter = InMemoryRateLimiter(
    max_requests=10,  # 10 tentatives
    window_seconds=300  # par 5 minutes
)


# =====================
# Middlewares de sécurité
# =====================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Ajoute les headers de sécurité HTTP à toutes les réponses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers de sécurité essentiels
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Cache-Control pour les réponses API
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        
        # Content-Security-Policy (adapté pour une API)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter un Request ID unique à chaque requête.
    Utile pour le tracing et le debugging.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Utiliser le X-Request-ID existant ou en générer un nouveau
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = secrets.token_urlsafe(16)
        
        # Stocker dans request.state pour accès dans les handlers
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Ajouter le Request ID dans la réponse
        response.headers["X-Request-ID"] = request_id
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting global."""
    
    async def dispatch(self, request: Request, call_next):
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Identifier le client (IP ou header X-Forwarded-For pour proxy)
        client_ip = self._get_client_ip(request)
        
        # Vérifier le rate limiting
        is_limited, remaining = rate_limiter.is_rate_limited(client_ip)
        
        if is_limited:
            reset_time = rate_limiter.get_reset_time(client_ip)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Trop de requêtes. Veuillez réessayer plus tard.",
                    "retry_after": reset_time
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_time)
                }
            )
        
        response = await call_next(request)
        
        # Ajouter les headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'IP client en tenant compte des proxies."""
        # Vérifier X-Forwarded-For si derrière un proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Prendre la première IP (client original)
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            for ip in ips:
                if ip not in TRUSTED_PROXIES:
                    return ip
        
        # Sinon, utiliser l'IP directe
        return request.client.host if request.client else "unknown"


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware de validation des requêtes entrantes."""
    
    # Taille maximale du corps de requête (10 MB par défaut)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))
    
    # Patterns dangereux à bloquer
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"\.\./",  # Path traversal
        r";\s*rm\s+-",  # Shell injection
        r"\$\{.*\}",  # Template injection
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Vérifier la taille du contenu
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Corps de requête trop volumineux"}
            )
        
        # Vérifier le Content-Type pour les requêtes avec corps
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not self._is_valid_content_type(content_type):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "Type de contenu non supporté"}
                )
        
        # Vérifier les patterns dangereux dans l'URL
        if self._contains_dangerous_pattern(str(request.url)):
            logger.warning(f"Requête suspecte bloquée: {request.url}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Requête invalide"}
            )
        
        return await call_next(request)
    
    def _is_valid_content_type(self, content_type: str) -> bool:
        """Vérifie que le Content-Type est autorisé."""
        allowed = [
            "application/json",
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ]
        return any(ct in content_type for ct in allowed)
    
    def _contains_dangerous_pattern(self, text: str) -> bool:
        """Vérifie si le texte contient des patterns dangereux."""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


# =====================
# Décorateurs de sécurité
# =====================

def rate_limit_auth(func: Callable) -> Callable:
    """
    Décorateur pour rate limiter les endpoints d'authentification.
    Plus restrictif que le rate limit global.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        if not request:
            # Essayer de trouver la requête dans args
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        if request:
            client_ip = request.client.host if request.client else "unknown"
            is_limited, _ = auth_rate_limiter.is_rate_limited(client_ip)
            
            if is_limited:
                reset_time = auth_rate_limiter.get_reset_time(client_ip)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Trop de tentatives. Réessayez dans {reset_time} secondes."
                )
        
        return await func(*args, **kwargs)
    
    return wrapper


def validate_object_id(field_name: str = "id"):
    """
    Décorateur pour valider les ObjectId MongoDB.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from bson import ObjectId
            from bson.errors import InvalidId
            
            value = kwargs.get(field_name)
            if value:
                try:
                    ObjectId(value)
                except InvalidId:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Format d'ID invalide: {field_name}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =====================
# Utilitaires de sécurité
# =====================

def generate_secure_token(length: int = 32) -> str:
    """Génère un token sécurisé cryptographiquement."""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str) -> str:
    """Hash des données sensibles (pour logs, etc.)."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def sanitize_log_data(data: dict) -> dict:
    """
    Masque les données sensibles pour les logs.
    """
    sensitive_fields = ["password", "token", "secret", "api_key", "authorization"]
    sanitized = data.copy()
    
    for key in sanitized:
        if any(field in key.lower() for field in sensitive_fields):
            sanitized[key] = "***REDACTED***"
    
    return sanitized


def validate_email_format(email: str) -> bool:
    """Valide le format d'un email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Valide la force d'un mot de passe.
    Retourne (is_valid, list_of_errors).
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Le mot de passe doit contenir au moins une majuscule")
    
    if not re.search(r'[a-z]', password):
        errors.append("Le mot de passe doit contenir au moins une minuscule")
    
    if not re.search(r'\d', password):
        errors.append("Le mot de passe doit contenir au moins un chiffre")
    
    return len(errors) == 0, errors


# =====================
# Protection CORS améliorée
# =====================

def get_cors_origins() -> List[str]:
    """
    Retourne la liste des origines CORS autorisées.
    """
    if "*" in ALLOWED_ORIGINS:
        return ["*"]
    
    return [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]


def is_origin_allowed(origin: str) -> bool:
    """Vérifie si une origine est autorisée."""
    if "*" in ALLOWED_ORIGINS:
        return True
    
    return origin in get_cors_origins()
