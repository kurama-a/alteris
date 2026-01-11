"""
Tests pour les modules de sécurité avancée.
"""
import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestBruteForceProtection:
    """Tests pour la protection contre les attaques par force brute."""
    
    @pytest.fixture
    def protection(self):
        from common.brute_force import BruteForceProtection
        return BruteForceProtection()
    
    @pytest.mark.asyncio
    async def test_allows_initial_attempts(self, protection):
        """Les premières tentatives sont autorisées."""
        is_allowed, error = await protection.record_attempt(
            email="test@example.com",
            ip_address="192.168.1.1",
            success=False
        )
        assert is_allowed is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_locks_after_max_attempts(self, protection):
        """Le compte est verrouillé après trop de tentatives."""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Simuler MAX_LOGIN_ATTEMPTS tentatives échouées
        for _ in range(5):  # MAX_LOGIN_ATTEMPTS par défaut
            await protection.record_attempt(email, ip, success=False)
        
        # La prochaine tentative devrait être bloquée
        is_allowed, error = await protection.record_attempt(email, ip, success=False)
        assert is_allowed is False
        assert "verrouillé" in error.lower()
    
    @pytest.mark.asyncio
    async def test_successful_login_resets_attempts(self, protection):
        """Un login réussi réinitialise les tentatives."""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Quelques tentatives échouées
        for _ in range(3):
            await protection.record_attempt(email, ip, success=False)
        
        # Login réussi
        protection.reset_attempts(email)
        
        # Les tentatives sont réinitialisées
        count = protection.get_attempt_count(email)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_unlock_account(self, protection):
        """Un admin peut déverrouiller un compte."""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Verrouiller le compte
        for _ in range(5):
            await protection.record_attempt(email, ip, success=False)
        
        # Vérifier qu'il est verrouillé
        is_locked, _ = protection.is_account_locked(email)
        assert is_locked
        
        # Déverrouiller
        result = await protection.unlock_account(email)
        assert result is True
        
        # Vérifier qu'il est déverrouillé
        is_locked, _ = protection.is_account_locked(email)
        assert not is_locked
    
    @pytest.mark.asyncio
    async def test_different_accounts_independent(self, protection):
        """Chaque compte a son propre compteur."""
        ip = "192.168.1.1"
        
        # Verrouiller le premier compte
        for _ in range(5):
            await protection.record_attempt("user1@example.com", ip, success=False)
        
        # Le deuxième compte devrait toujours être accessible
        is_allowed, _ = await protection.record_attempt(
            "user2@example.com", ip, success=False
        )
        assert is_allowed is True
    
    def test_get_locked_accounts(self, protection):
        """Liste les comptes verrouillés."""
        # Initialement vide
        locked = protection.get_locked_accounts()
        assert locked == []


class TestSanitization:
    """Tests pour le module de sanitisation."""
    
    def test_sanitize_string_basic(self):
        """Sanitisation basique des chaînes."""
        from common.sanitization import sanitize_string
        
        result = sanitize_string("  Hello World  ")
        assert result == "Hello World"
    
    def test_sanitize_string_max_length(self):
        """Limite la longueur des chaînes."""
        from common.sanitization import sanitize_string
        
        long_string = "a" * 1000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_html(self):
        """Échappe les caractères HTML."""
        from common.sanitization import sanitize_html
        
        result = sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_email(self):
        """Normalise les emails."""
        from common.sanitization import sanitize_email
        
        result = sanitize_email("  Test@Example.COM  ")
        assert result == "test@example.com"
    
    def test_sanitize_filename(self):
        """Sanitise les noms de fichiers."""
        from common.sanitization import sanitize_filename
        
        # Path traversal
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        
        # Caractères dangereux
        result = sanitize_filename('file<>:"|?*.txt')
        assert "<" not in result
        assert ">" not in result
    
    def test_detect_xss(self):
        """Détecte les tentatives XSS."""
        from common.sanitization import detect_xss
        
        assert detect_xss("<script>alert('xss')</script>") is True
        assert detect_xss("onclick=alert(1)") is True
        assert detect_xss("Hello World") is False
    
    def test_detect_nosql_injection(self):
        """Détecte les injections NoSQL."""
        from common.sanitization import detect_nosql_injection
        
        assert detect_nosql_injection({"$gt": ""}) is True
        assert detect_nosql_injection("$where: function()") is True
        assert detect_nosql_injection({"name": "John"}) is False
    
    def test_detect_path_traversal(self):
        """Détecte les path traversal."""
        from common.sanitization import detect_path_traversal
        
        assert detect_path_traversal("../etc/passwd") is True
        assert detect_path_traversal("%2e%2e/etc/passwd") is True
        assert detect_path_traversal("normal/path") is False
    
    def test_is_safe_input(self):
        """Vérifie si une entrée est sûre."""
        from common.sanitization import is_safe_input
        
        is_safe, threat = is_safe_input("Hello World")
        assert is_safe is True
        assert threat is None
        
        is_safe, threat = is_safe_input("<script>alert(1)</script>")
        assert is_safe is False
        assert threat == "xss"
    
    def test_validate_object_id(self):
        """Valide les ObjectId MongoDB."""
        from common.sanitization import validate_object_id
        
        assert validate_object_id("507f1f77bcf86cd799439011") is True
        assert validate_object_id("invalid") is False
        assert validate_object_id("507f1f77bcf86cd79943901") is False  # Trop court
    
    def test_sanitize_for_mongodb(self):
        """Sanitise pour MongoDB."""
        from common.sanitization import sanitize_for_mongodb
        
        # Les clés commençant par $ sont supprimées
        result = sanitize_for_mongodb({"$gt": 5, "name": "test"})
        assert "$gt" not in result
        assert "name" in result


class TestJWTManager:
    """Tests pour le gestionnaire JWT."""
    
    @pytest.fixture
    def manager(self):
        from common.jwt_manager import TokenManager
        return TokenManager()
    
    def test_create_access_token(self, manager):
        """Crée un access token valide."""
        token, jti = manager.create_access_token(
            user_id="123",
            email="test@example.com",
            role="apprenti"
        )
        
        assert token is not None
        assert len(token) > 0
        assert jti is not None
    
    def test_verify_access_token(self, manager):
        """Vérifie un access token."""
        token, _ = manager.create_access_token(
            user_id="123",
            email="test@example.com",
            role="apprenti"
        )
        
        data = manager.verify_token(token, expected_type="access")
        
        assert data is not None
        assert data.user_id == "123"
        assert data.email == "test@example.com"
        assert data.role == "apprenti"
    
    def test_verify_wrong_token_type(self, manager):
        """Rejette un token avec le mauvais type."""
        access_token, _ = manager.create_access_token(
            user_id="123",
            email="test@example.com",
            role="apprenti"
        )
        
        # Essayer de vérifier comme refresh token
        data = manager.verify_token(access_token, expected_type="refresh")
        assert data is None
    
    @pytest.mark.asyncio
    async def test_create_token_pair(self, manager):
        """Crée une paire de tokens."""
        pair = await manager.create_token_pair(
            user_id="123",
            email="test@example.com",
            role="apprenti"
        )
        
        assert pair.access_token is not None
        assert pair.refresh_token is not None
        assert pair.token_type == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, manager):
        """Les refresh tokens sont tournés à chaque utilisation."""
        pair = await manager.create_token_pair(
            user_id="123",
            email="test@example.com",
            role="apprenti"
        )
        
        # Utiliser le refresh token
        result = await manager.refresh_access_token(pair.refresh_token)
        assert result is not None
        
        new_access, new_refresh = result
        assert new_access != pair.access_token
        assert new_refresh != pair.refresh_token
        
        # L'ancien refresh token ne devrait plus fonctionner
        result2 = await manager.refresh_access_token(pair.refresh_token)
        assert result2 is None
    
    @pytest.mark.asyncio
    async def test_revoke_token(self, manager):
        """Révoque un token."""
        token, jti = manager.create_access_token(
            user_id="123",
            email="test@example.com",
            role="apprenti"
        )
        
        # Révoquer
        result = await manager.revoke_token(token)
        assert result is True
        
        # Le token ne devrait plus être valide
        data = manager.verify_token(token)
        assert data is None
    
    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self, manager):
        """Révoque tous les tokens d'un utilisateur."""
        user_id = "123"
        
        # Créer plusieurs sessions
        await manager.create_token_pair(user_id, "test@example.com", "apprenti")
        await manager.create_token_pair(user_id, "test@example.com", "apprenti")
        
        # Révoquer tout
        count = await manager.revoke_all_user_tokens(user_id)
        assert count == 2
        
        # Plus de sessions
        sessions = manager.get_user_sessions_count(user_id)
        assert sessions == 0


class TestAuditService:
    """Tests pour le service d'audit."""
    
    @pytest.fixture
    def service(self):
        from common.audit import AuditService
        return AuditService()
    
    @pytest.mark.asyncio
    async def test_log_auth_success(self, service):
        """Log une authentification réussie."""
        await service.log_auth_success(
            user_id="123",
            user_email="test@example.com",
            ip_address="192.168.1.1"
        )
        
        events = service.get_recent_events(limit=1)
        assert len(events) == 1
        assert events[0]["event_type"] == "auth.login.success"
    
    @pytest.mark.asyncio
    async def test_log_auth_failure(self, service):
        """Log une authentification échouée."""
        await service.log_auth_failure(
            email="test@example.com",
            ip_address="192.168.1.1",
            reason="Invalid password"
        )
        
        events = service.get_recent_events(limit=1)
        assert len(events) == 1
        assert events[0]["event_type"] == "auth.login.failure"
        assert events[0]["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_security_events(self, service):
        """Récupère les événements de sécurité."""
        from common.audit import AuditEventType
        
        await service.log_security_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address="192.168.1.1",
            details={"endpoint": "/api/login"}
        )
        
        events = service.get_security_events(limit=10)
        assert len(events) >= 1
    
    @pytest.mark.asyncio
    async def test_get_user_activity(self, service):
        """Récupère l'activité d'un utilisateur."""
        user_id = "123"
        
        await service.log_data_access(
            user_id=user_id,
            resource_type="apprenti",
            resource_id="456"
        )
        
        activity = service.get_user_activity(user_id)
        assert len(activity) >= 1
        assert activity[0]["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_filter_by_event_type(self, service):
        """Filtre les événements par type."""
        from common.audit import AuditEventType
        
        await service.log_auth_success("1", "a@b.com", "1.1.1.1")
        await service.log_auth_failure("b@c.com", "1.1.1.1", "bad")
        
        events = service.get_recent_events(
            event_type=AuditEventType.LOGIN_SUCCESS
        )
        
        for event in events:
            assert event["event_type"] == "auth.login.success"