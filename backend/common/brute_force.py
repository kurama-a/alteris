"""
Module de protection contre les attaques par force brute.
Account lockout et détection des tentatives suspectes.
"""
import os
import time
import asyncio
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from enum import Enum

from common.audit import audit_service, AuditEventType


# =====================
# Configuration
# =====================

# Nombre de tentatives avant verrouillage
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))

# Durée du verrouillage en secondes (30 minutes par défaut)
LOCKOUT_DURATION = int(os.getenv("LOCKOUT_DURATION", "1800"))

# Fenêtre de temps pour compter les tentatives (15 minutes)
ATTEMPT_WINDOW = int(os.getenv("ATTEMPT_WINDOW", "900"))

# Durée de verrouillage progressive (doublement à chaque lockout)
PROGRESSIVE_LOCKOUT = os.getenv("PROGRESSIVE_LOCKOUT", "true").lower() == "true"

# Seuil pour détecter une attaque distribuée (tentatives sur plusieurs comptes depuis une IP)
DISTRIBUTED_ATTACK_THRESHOLD = int(os.getenv("DISTRIBUTED_ATTACK_THRESHOLD", "10"))


class LockoutReason(str, Enum):
    """Raisons de verrouillage."""
    TOO_MANY_ATTEMPTS = "too_many_login_attempts"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ADMIN_LOCK = "admin_locked"
    DISTRIBUTED_ATTACK = "distributed_attack_detected"


@dataclass
class LoginAttempt:
    """Représente une tentative de connexion."""
    timestamp: float
    email: str
    ip_address: str
    success: bool
    user_agent: Optional[str] = None


@dataclass
class AccountLockout:
    """Représente un verrouillage de compte."""
    email: str
    locked_at: float
    unlock_at: float
    reason: LockoutReason
    attempt_count: int
    lockout_count: int = 1  # Nombre de verrouillages consécutifs


@dataclass
class IPLockout:
    """Représente un verrouillage d'IP."""
    ip_address: str
    locked_at: float
    unlock_at: float
    reason: LockoutReason
    targeted_accounts: List[str] = field(default_factory=list)


class BruteForceProtection:
    """
    Protection contre les attaques par force brute.
    Gère le verrouillage des comptes et des IPs.
    """
    
    def __init__(self):
        # Tentatives par email
        self._attempts_by_email: Dict[str, List[LoginAttempt]] = defaultdict(list)
        # Tentatives par IP
        self._attempts_by_ip: Dict[str, List[LoginAttempt]] = defaultdict(list)
        # Comptes verrouillés
        self._locked_accounts: Dict[str, AccountLockout] = {}
        # IPs verrouillées
        self._locked_ips: Dict[str, IPLockout] = {}
        # Historique des lockouts par email (pour verrouillage progressif)
        self._lockout_history: Dict[str, int] = defaultdict(int)
        # Lock pour thread-safety
        self._lock = asyncio.Lock()
    
    async def record_attempt(
        self,
        email: str,
        ip_address: str,
        success: bool,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Enregistre une tentative de connexion.
        Retourne (is_allowed, error_message).
        """
        async with self._lock:
            now = time.time()
            
            # Vérifier si le compte est verrouillé
            if email in self._locked_accounts:
                lockout = self._locked_accounts[email]
                if now < lockout.unlock_at:
                    remaining = int(lockout.unlock_at - now)
                    return False, f"Compte verrouillé. Réessayez dans {remaining // 60} minutes."
                else:
                    # Débloquer le compte
                    del self._locked_accounts[email]
            
            # Vérifier si l'IP est verrouillée
            if ip_address in self._locked_ips:
                lockout = self._locked_ips[ip_address]
                if now < lockout.unlock_at:
                    remaining = int(lockout.unlock_at - now)
                    return False, f"Trop de tentatives depuis cette adresse. Réessayez dans {remaining // 60} minutes."
                else:
                    del self._locked_ips[ip_address]
            
            # Créer l'enregistrement de tentative
            attempt = LoginAttempt(
                timestamp=now,
                email=email,
                ip_address=ip_address,
                success=success,
                user_agent=user_agent
            )
            
            # Enregistrer la tentative
            self._attempts_by_email[email].append(attempt)
            self._attempts_by_ip[ip_address].append(attempt)
            
            # Nettoyer les anciennes tentatives
            self._cleanup_old_attempts(email, ip_address, now)
            
            if not success:
                # Vérifier si on doit verrouiller le compte
                should_lock, reason = self._should_lock_account(email, now)
                if should_lock:
                    await self._lock_account(email, reason)
                    
                    # Log l'événement
                    await audit_service.log_security_event(
                        event_type=AuditEventType.BRUTE_FORCE_DETECTED,
                        ip_address=ip_address,
                        details={
                            "email": email,
                            "attempt_count": len(self._get_recent_attempts(email, now)),
                            "reason": reason.value
                        }
                    )
                    
                    return False, "Compte verrouillé suite à trop de tentatives échouées."
                
                # Vérifier si on doit verrouiller l'IP (attaque distribuée)
                should_lock_ip, targeted = self._should_lock_ip(ip_address, now)
                if should_lock_ip:
                    await self._lock_ip(ip_address, targeted)
                    
                    await audit_service.log_security_event(
                        event_type=AuditEventType.BRUTE_FORCE_DETECTED,
                        ip_address=ip_address,
                        details={
                            "type": "distributed_attack",
                            "targeted_accounts": targeted[:10],  # Limiter pour les logs
                            "account_count": len(targeted)
                        }
                    )
                    
                    return False, "Activité suspecte détectée. Accès temporairement bloqué."
            
            return True, None
    
    def _cleanup_old_attempts(self, email: str, ip_address: str, now: float) -> None:
        """Nettoie les tentatives expirées."""
        cutoff = now - ATTEMPT_WINDOW
        
        self._attempts_by_email[email] = [
            a for a in self._attempts_by_email[email]
            if a.timestamp > cutoff
        ]
        
        self._attempts_by_ip[ip_address] = [
            a for a in self._attempts_by_ip[ip_address]
            if a.timestamp > cutoff
        ]
    
    def _get_recent_attempts(self, email: str, now: float) -> List[LoginAttempt]:
        """Récupère les tentatives récentes pour un email."""
        cutoff = now - ATTEMPT_WINDOW
        return [
            a for a in self._attempts_by_email.get(email, [])
            if a.timestamp > cutoff and not a.success
        ]
    
    def _should_lock_account(self, email: str, now: float) -> Tuple[bool, Optional[LockoutReason]]:
        """Détermine si un compte doit être verrouillé."""
        recent_failures = self._get_recent_attempts(email, now)
        
        if len(recent_failures) >= MAX_LOGIN_ATTEMPTS:
            return True, LockoutReason.TOO_MANY_ATTEMPTS
        
        return False, None
    
    def _should_lock_ip(self, ip_address: str, now: float) -> Tuple[bool, List[str]]:
        """
        Détermine si une IP doit être verrouillée (attaque distribuée).
        Retourne (should_lock, list_of_targeted_emails).
        """
        cutoff = now - ATTEMPT_WINDOW
        recent = [
            a for a in self._attempts_by_ip.get(ip_address, [])
            if a.timestamp > cutoff and not a.success
        ]
        
        # Compter les comptes distincts ciblés
        targeted_emails = list(set(a.email for a in recent))
        
        if len(targeted_emails) >= DISTRIBUTED_ATTACK_THRESHOLD:
            return True, targeted_emails
        
        return False, []
    
    async def _lock_account(self, email: str, reason: LockoutReason) -> None:
        """Verrouille un compte."""
        now = time.time()
        
        # Verrouillage progressif
        lockout_count = self._lockout_history[email] + 1
        self._lockout_history[email] = lockout_count
        
        if PROGRESSIVE_LOCKOUT:
            # Doubler la durée à chaque verrouillage (max 24h)
            duration = min(LOCKOUT_DURATION * (2 ** (lockout_count - 1)), 86400)
        else:
            duration = LOCKOUT_DURATION
        
        self._locked_accounts[email] = AccountLockout(
            email=email,
            locked_at=now,
            unlock_at=now + duration,
            reason=reason,
            attempt_count=len(self._get_recent_attempts(email, now)),
            lockout_count=lockout_count
        )
    
    async def _lock_ip(self, ip_address: str, targeted_accounts: List[str]) -> None:
        """Verrouille une IP."""
        now = time.time()
        
        self._locked_ips[ip_address] = IPLockout(
            ip_address=ip_address,
            locked_at=now,
            unlock_at=now + LOCKOUT_DURATION,
            reason=LockoutReason.DISTRIBUTED_ATTACK,
            targeted_accounts=targeted_accounts
        )
    
    async def unlock_account(self, email: str, admin_user_id: Optional[str] = None) -> bool:
        """Déverrouille manuellement un compte (admin)."""
        async with self._lock:
            if email in self._locked_accounts:
                del self._locked_accounts[email]
                # Reset l'historique de lockout
                self._lockout_history[email] = 0
                
                if admin_user_id:
                    await audit_service.log_user_action(
                        event_type=AuditEventType.USER_UNLOCK,
                        user_id=admin_user_id,
                        target_user_id=email,
                        action="manual_unlock",
                        details={"unlocked_by": "admin"}
                    )
                
                return True
            return False
    
    async def unlock_ip(self, ip_address: str, admin_user_id: Optional[str] = None) -> bool:
        """Déverrouille manuellement une IP (admin)."""
        async with self._lock:
            if ip_address in self._locked_ips:
                del self._locked_ips[ip_address]
                return True
            return False
    
    def is_account_locked(self, email: str) -> Tuple[bool, Optional[int]]:
        """
        Vérifie si un compte est verrouillé.
        Retourne (is_locked, seconds_remaining).
        """
        if email not in self._locked_accounts:
            return False, None
        
        lockout = self._locked_accounts[email]
        now = time.time()
        
        if now >= lockout.unlock_at:
            return False, None
        
        return True, int(lockout.unlock_at - now)
    
    def is_ip_locked(self, ip_address: str) -> Tuple[bool, Optional[int]]:
        """
        Vérifie si une IP est verrouillée.
        Retourne (is_locked, seconds_remaining).
        """
        if ip_address not in self._locked_ips:
            return False, None
        
        lockout = self._locked_ips[ip_address]
        now = time.time()
        
        if now >= lockout.unlock_at:
            return False, None
        
        return True, int(lockout.unlock_at - now)
    
    def get_locked_accounts(self) -> List[Dict]:
        """Retourne la liste des comptes verrouillés."""
        now = time.time()
        return [
            {
                "email": lockout.email,
                "locked_at": datetime.fromtimestamp(lockout.locked_at, timezone.utc).isoformat(),
                "unlock_at": datetime.fromtimestamp(lockout.unlock_at, timezone.utc).isoformat(),
                "remaining_seconds": max(0, int(lockout.unlock_at - now)),
                "reason": lockout.reason.value,
                "attempt_count": lockout.attempt_count,
                "lockout_count": lockout.lockout_count
            }
            for lockout in self._locked_accounts.values()
            if lockout.unlock_at > now
        ]
    
    def get_locked_ips(self) -> List[Dict]:
        """Retourne la liste des IPs verrouillées."""
        now = time.time()
        return [
            {
                "ip_address": lockout.ip_address,
                "locked_at": datetime.fromtimestamp(lockout.locked_at, timezone.utc).isoformat(),
                "unlock_at": datetime.fromtimestamp(lockout.unlock_at, timezone.utc).isoformat(),
                "remaining_seconds": max(0, int(lockout.unlock_at - now)),
                "reason": lockout.reason.value,
                "targeted_accounts_count": len(lockout.targeted_accounts)
            }
            for lockout in self._locked_ips.values()
            if lockout.unlock_at > now
        ]
    
    def get_attempt_count(self, email: str) -> int:
        """Retourne le nombre de tentatives récentes pour un email."""
        now = time.time()
        return len(self._get_recent_attempts(email, now))
    
    def reset_attempts(self, email: str) -> None:
        """Réinitialise les tentatives pour un email (après login réussi)."""
        if email in self._attempts_by_email:
            self._attempts_by_email[email] = []
        # Reset aussi l'historique de lockout après un login réussi
        self._lockout_history[email] = 0


# Instance globale
brute_force_protection = BruteForceProtection()
