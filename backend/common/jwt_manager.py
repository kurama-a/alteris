"""
Module de gestion des tokens JWT amélioré.
Refresh tokens, révocation et gestion de session.
"""
import os
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from collections import defaultdict
import asyncio

from jose import jwt, JWTError
from passlib.context import CryptContext


# =====================
# Configuration
# =====================

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-do-not-use-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# Configuration du hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class TokenPair:
    """Paire de tokens access + refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_expires_in: int = REFRESH_TOKEN_EXPIRE_DAYS * 86400


@dataclass
class TokenData:
    """Données extraites d'un token."""
    user_id: str
    email: str
    role: str
    token_type: str  # "access" ou "refresh"
    jti: str  # JWT ID unique
    exp: datetime
    iat: datetime


class TokenManager:
    """
    Gestionnaire de tokens JWT avec support pour:
    - Access tokens (courte durée)
    - Refresh tokens (longue durée)
    - Révocation de tokens
    - Gestion des sessions
    """
    
    def __init__(self):
        # Tokens révoqués (jti -> expiration)
        self._revoked_tokens: Dict[str, float] = {}
        # Sessions actives par utilisateur
        self._user_sessions: Dict[str, List[str]] = defaultdict(list)
        # Refresh tokens actifs (hash -> user_id)
        self._active_refresh_tokens: Dict[str, str] = {}
        # Lock pour thread-safety
        self._lock = asyncio.Lock()
        # Nombre max de sessions par utilisateur
        self.max_sessions_per_user = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
    
    def _generate_jti(self) -> str:
        """Génère un identifiant unique pour le token."""
        return secrets.token_urlsafe(32)
    
    def _hash_token(self, token: str) -> str:
        """Hash un token pour le stockage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Crée un access token.
        Retourne (token, jti).
        """
        jti = self._generate_jti()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "jti": jti,
            "iat": now,
            "exp": expire,
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token, jti
    
    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        role: str
    ) -> Tuple[str, str]:
        """
        Crée un refresh token.
        Retourne (token, jti).
        """
        jti = self._generate_jti()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "refresh",
            "jti": jti,
            "iat": now,
            "exp": expire,
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token, jti
    
    async def create_token_pair(
        self,
        user_id: str,
        email: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> TokenPair:
        """
        Crée une paire access + refresh token.
        """
        access_token, access_jti = self.create_access_token(
            user_id, email, role, additional_claims
        )
        refresh_token, refresh_jti = self.create_refresh_token(
            user_id, email, role
        )
        
        async with self._lock:
            # Enregistrer le refresh token
            token_hash = self._hash_token(refresh_token)
            self._active_refresh_tokens[token_hash] = user_id
            
            # Gérer les sessions
            await self._manage_sessions(user_id, refresh_jti)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    async def _manage_sessions(self, user_id: str, new_jti: str) -> None:
        """Gère le nombre de sessions par utilisateur."""
        sessions = self._user_sessions[user_id]
        sessions.append(new_jti)
        
        # Si trop de sessions, révoquer les plus anciennes
        while len(sessions) > self.max_sessions_per_user:
            old_jti = sessions.pop(0)
            await self._revoke_jti(old_jti)
    
    def verify_token(self, token: str, expected_type: str = "access") -> Optional[TokenData]:
        """
        Vérifie et décode un token.
        Retourne TokenData si valide, None sinon.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Vérifier le type de token
            if payload.get("type") != expected_type:
                return None
            
            # Vérifier si révoqué
            jti = payload.get("jti")
            if jti and self._is_revoked(jti):
                return None
            
            return TokenData(
                user_id=payload["sub"],
                email=payload["email"],
                role=payload["role"],
                token_type=payload["type"],
                jti=payload.get("jti", ""),
                exp=datetime.fromtimestamp(payload["exp"], timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], timezone.utc)
            )
            
        except JWTError:
            return None
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Utilise un refresh token pour obtenir un nouvel access token.
        Retourne (new_access_token, new_refresh_token) ou None.
        """
        # Vérifier le refresh token
        token_data = self.verify_token(refresh_token, expected_type="refresh")
        if not token_data:
            return None
        
        # Vérifier que le refresh token est actif
        token_hash = self._hash_token(refresh_token)
        async with self._lock:
            if token_hash not in self._active_refresh_tokens:
                return None
        
        # Créer une nouvelle paire de tokens (rotation des tokens)
        token_pair = await self.create_token_pair(
            user_id=token_data.user_id,
            email=token_data.email,
            role=token_data.role,
            additional_claims=additional_claims
        )
        
        # Révoquer l'ancien refresh token
        await self.revoke_token(refresh_token)
        
        return token_pair.access_token, token_pair.refresh_token
    
    async def revoke_token(self, token: str) -> bool:
        """Révoque un token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti:
                await self._revoke_jti(jti, exp)
            
            # Si c'est un refresh token, le retirer des tokens actifs
            if payload.get("type") == "refresh":
                token_hash = self._hash_token(token)
                async with self._lock:
                    self._active_refresh_tokens.pop(token_hash, None)
            
            return True
            
        except JWTError:
            return False
    
    async def _revoke_jti(self, jti: str, exp: Optional[float] = None) -> None:
        """Révoque un token par son JTI."""
        async with self._lock:
            # Stocker jusqu'à l'expiration + marge
            if exp:
                self._revoked_tokens[jti] = exp + 3600  # +1h de marge
            else:
                # Par défaut, garder 24h
                self._revoked_tokens[jti] = datetime.now(timezone.utc).timestamp() + 86400
    
    def _is_revoked(self, jti: str) -> bool:
        """Vérifie si un JTI est révoqué."""
        if jti in self._revoked_tokens:
            # Nettoyer si expiré
            if self._revoked_tokens[jti] < datetime.now(timezone.utc).timestamp():
                del self._revoked_tokens[jti]
                return False
            return True
        return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Révoque tous les tokens d'un utilisateur.
        Retourne le nombre de sessions révoquées.
        """
        async with self._lock:
            # Révoquer toutes les sessions
            sessions = self._user_sessions.get(user_id, [])
            for jti in sessions:
                self._revoked_tokens[jti] = datetime.now(timezone.utc).timestamp() + 86400
            
            count = len(sessions)
            self._user_sessions[user_id] = []
            
            # Retirer les refresh tokens
            tokens_to_remove = [
                h for h, uid in self._active_refresh_tokens.items()
                if uid == user_id
            ]
            for token_hash in tokens_to_remove:
                del self._active_refresh_tokens[token_hash]
            
            return count
    
    async def cleanup_expired(self) -> int:
        """Nettoie les tokens révoqués expirés."""
        now = datetime.now(timezone.utc).timestamp()
        
        async with self._lock:
            expired = [
                jti for jti, exp in self._revoked_tokens.items()
                if exp < now
            ]
            for jti in expired:
                del self._revoked_tokens[jti]
            
            return len(expired)
    
    def get_user_sessions_count(self, user_id: str) -> int:
        """Retourne le nombre de sessions actives pour un utilisateur."""
        return len(self._user_sessions.get(user_id, []))
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du gestionnaire de tokens."""
        return {
            "revoked_tokens_count": len(self._revoked_tokens),
            "active_refresh_tokens": len(self._active_refresh_tokens),
            "users_with_sessions": len(self._user_sessions),
            "max_sessions_per_user": self.max_sessions_per_user
        }


# Instance globale
token_manager = TokenManager()


# =====================
# Fonctions utilitaires
# =====================

async def create_tokens_for_user(
    user_id: str,
    email: str,
    role: str,
    **additional_claims
) -> TokenPair:
    """Crée une paire de tokens pour un utilisateur."""
    return await token_manager.create_token_pair(
        user_id=user_id,
        email=email,
        role=role,
        additional_claims=additional_claims if additional_claims else None
    )


def verify_access_token(token: str) -> Optional[TokenData]:
    """Vérifie un access token."""
    return token_manager.verify_token(token, expected_type="access")


async def refresh_tokens(refresh_token: str) -> Optional[Tuple[str, str]]:
    """Rafraîchit les tokens."""
    return await token_manager.refresh_access_token(refresh_token)


async def logout_user(user_id: str) -> int:
    """Déconnecte un utilisateur de toutes ses sessions."""
    return await token_manager.revoke_all_user_tokens(user_id)
