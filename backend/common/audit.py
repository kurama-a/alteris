"""
Module d'audit et logging sécurisé pour le backend Alteris.
Traçabilité complète des actions sensibles.
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field, asdict
from functools import wraps
from collections import deque

from fastapi import Request


# =====================
# Configuration
# =====================

AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "audit.log")
AUDIT_LOG_MAX_MEMORY = int(os.getenv("AUDIT_LOG_MAX_MEMORY", "1000"))  # Entrées en mémoire

# Logger dédié pour l'audit
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Handler fichier pour l'audit (si configuré)
if AUDIT_LOG_ENABLED and AUDIT_LOG_FILE:
    try:
        file_handler = logging.FileHandler(AUDIT_LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        audit_logger.addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Impossible de créer le fichier d'audit: {e}")


# =====================
# Types d'événements d'audit
# =====================

class AuditEventType(str, Enum):
    """Types d'événements d'audit."""
    # Authentification
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET_REQUEST = "auth.password.reset_request"
    
    # Gestion des utilisateurs
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role.change"
    USER_LOCK = "user.lock"
    USER_UNLOCK = "user.unlock"
    
    # Accès aux données
    DATA_ACCESS = "data.access"
    DATA_EXPORT = "data.export"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    
    # Sécurité
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    INVALID_TOKEN = "security.invalid_token"
    PERMISSION_DENIED = "security.permission_denied"
    BRUTE_FORCE_DETECTED = "security.brute_force"
    
    # Système
    CONFIG_CHANGE = "system.config.change"
    SERVICE_START = "system.service.start"
    SERVICE_STOP = "system.service.stop"
    ERROR = "system.error"


class AuditSeverity(str, Enum):
    """Niveaux de sévérité des événements."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =====================
# Structure d'un événement d'audit
# =====================

@dataclass
class AuditEvent:
    """Représente un événement d'audit."""
    event_type: AuditEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Contexte utilisateur
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    
    # Contexte requête
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # Détails de l'événement
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Résultat
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'événement en dictionnaire."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data
    
    def to_json(self) -> str:
        """Convertit l'événement en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


# =====================
# Service d'audit
# =====================

class AuditService:
    """
    Service centralisé pour l'audit et la traçabilité.
    Stocke en mémoire et écrit dans les logs.
    """
    
    def __init__(self, max_memory_events: int = AUDIT_LOG_MAX_MEMORY):
        self._events: deque = deque(maxlen=max_memory_events)
        self._lock = asyncio.Lock()
        self._enabled = AUDIT_LOG_ENABLED
    
    async def log(self, event: AuditEvent) -> None:
        """Enregistre un événement d'audit."""
        if not self._enabled:
            return
        
        async with self._lock:
            self._events.append(event)
        
        # Écrire dans le logger
        log_method = getattr(audit_logger, event.severity.value, audit_logger.info)
        log_method(event.to_json())
    
    async def log_auth_success(
        self,
        user_id: str,
        user_email: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log une authentification réussie."""
        await self.log(AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=True
        ))
    
    async def log_auth_failure(
        self,
        email: str,
        ip_address: str,
        reason: str,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log une tentative d'authentification échouée."""
        await self.log(AuditEvent(
            event_type=AuditEventType.LOGIN_FAILURE,
            severity=AuditSeverity.WARNING,
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=False,
            error_message=reason,
            details={"attempted_email": email}
        ))
    
    async def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log un accès aux données."""
        await self.log(AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            request_id=request_id
        ))
    
    async def log_security_event(
        self,
        event_type: AuditEventType,
        ip_address: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log un événement de sécurité."""
        await self.log(AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            request_id=request_id,
            details=details,
            success=False
        ))
    
    async def log_user_action(
        self,
        event_type: AuditEventType,
        user_id: str,
        target_user_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log une action sur un utilisateur."""
        await self.log(AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            resource_type="user",
            resource_id=target_user_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            request_id=request_id
        ))
    
    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None
    ) -> List[Dict[str, Any]]:
        """Récupère les événements récents avec filtres optionnels."""
        events = list(self._events)
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if severity:
            events = [e for e in events if e.severity == severity]
        
        # Retourner les plus récents en premier
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in events[:limit]]
    
    def get_security_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les événements de sécurité récents."""
        security_types = {
            AuditEventType.RATE_LIMIT_EXCEEDED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.INVALID_TOKEN,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.BRUTE_FORCE_DETECTED,
            AuditEventType.LOGIN_FAILURE
        }
        
        events = [e for e in self._events if e.event_type in security_types]
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in events[:limit]]
    
    def get_user_activity(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère l'activité d'un utilisateur spécifique."""
        return self.get_recent_events(limit=limit, user_id=user_id)


# Instance globale du service d'audit
audit_service = AuditService()


# =====================
# Décorateur d'audit
# =====================

def audit_action(
    event_type: AuditEventType,
    resource_type: Optional[str] = None,
    get_resource_id: Optional[callable] = None
):
    """
    Décorateur pour auditer automatiquement les actions.
    
    Usage:
        @audit_action(AuditEventType.DATA_UPDATE, resource_type="apprenti")
        async def update_apprenti(apprenti_id: str, data: dict):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraire le contexte si disponible
            request: Optional[Request] = kwargs.get("request")
            current_user = kwargs.get("current_user")
            
            user_id = None
            ip_address = None
            request_id = None
            
            if current_user:
                user_id = str(current_user.get("_id", current_user.get("id")))
            
            if request:
                ip_address = request.client.host if request.client else None
                request_id = request.headers.get("X-Request-ID")
            
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception:
                    pass
            
            try:
                result = await func(*args, **kwargs)
                
                # Log succès
                await audit_service.log(AuditEvent(
                    event_type=event_type,
                    severity=AuditSeverity.INFO,
                    user_id=user_id,
                    ip_address=ip_address,
                    request_id=request_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    success=True
                ))
                
                return result
                
            except Exception as e:
                # Log échec
                await audit_service.log(AuditEvent(
                    event_type=event_type,
                    severity=AuditSeverity.ERROR,
                    user_id=user_id,
                    ip_address=ip_address,
                    request_id=request_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    success=False,
                    error_message=str(e)
                ))
                raise
        
        return wrapper
    return decorator


# =====================
# Utilitaires
# =====================

def extract_request_context(request: Request) -> Dict[str, Any]:
    """Extrait le contexte d'une requête pour l'audit."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "endpoint": str(request.url.path),
        "method": request.method,
        "request_id": request.headers.get("X-Request-ID")
    }
