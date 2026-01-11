"""
Tests pour le module de sécurité.
"""
import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from starlette.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.security import (
    InMemoryRateLimiter,
    generate_secure_token,
    hash_sensitive_data,
    sanitize_log_data,
    validate_email_format,
    validate_password_strength,
    get_cors_origins,
)


class TestInMemoryRateLimiter:
    """Tests pour le rate limiter en mémoire."""
    
    def test_allows_requests_under_limit(self):
        """Le rate limiter autorise les requêtes sous la limite."""
        limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            is_limited, remaining = limiter.is_rate_limited("test-client")
            assert not is_limited, f"Request {i+1} should not be limited"
            assert remaining == 4 - i
    
    def test_blocks_requests_over_limit(self):
        """Le rate limiter bloque les requêtes au-delà de la limite."""
        limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
        
        # Épuiser la limite
        for _ in range(3):
            limiter.is_rate_limited("test-client")
        
        # La 4ème requête doit être bloquée
        is_limited, remaining = limiter.is_rate_limited("test-client")
        assert is_limited
        assert remaining == 0
    
    def test_different_clients_independent(self):
        """Chaque client a son propre compteur."""
        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        
        # Client 1 épuise sa limite
        limiter.is_rate_limited("client1")
        limiter.is_rate_limited("client1")
        is_limited, _ = limiter.is_rate_limited("client1")
        assert is_limited
        
        # Client 2 devrait toujours pouvoir accéder
        is_limited, remaining = limiter.is_rate_limited("client2")
        assert not is_limited
        assert remaining == 1
    
    def test_reset_after_window(self):
        """Le compteur se réinitialise après la fenêtre de temps."""
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=1)
        
        # Épuiser la limite
        limiter.is_rate_limited("test-client")
        is_limited, _ = limiter.is_rate_limited("test-client")
        assert is_limited
        
        # Attendre que la fenêtre expire
        time.sleep(1.1)
        
        # Devrait être autorisé à nouveau
        is_limited, _ = limiter.is_rate_limited("test-client")
        assert not is_limited
    
    def test_get_reset_time(self):
        """get_reset_time retourne le temps restant."""
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
        
        # Faire une requête
        limiter.is_rate_limited("test-client")
        
        reset_time = limiter.get_reset_time("test-client")
        assert 0 < reset_time <= 60


class TestSecurityUtils:
    """Tests pour les utilitaires de sécurité."""
    
    def test_generate_secure_token(self):
        """Génère des tokens sécurisés uniques."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        assert token1 != token2
        assert len(token1) > 20
    
    def test_generate_secure_token_custom_length(self):
        """Génère des tokens avec longueur personnalisée."""
        token = generate_secure_token(length=64)
        assert len(token) > 60  # base64 peut être légèrement plus long
    
    def test_hash_sensitive_data(self):
        """Hash les données de manière cohérente."""
        data = "test-data"
        hash1 = hash_sensitive_data(data)
        hash2 = hash_sensitive_data(data)
        
        assert hash1 == hash2
        assert len(hash1) == 16
        assert data not in hash1
    
    def test_sanitize_log_data(self):
        """Masque les données sensibles pour les logs."""
        data = {
            "username": "john",
            "password": "secret123",
            "email": "john@example.com",
            "api_key": "abc123",
            "user_token": "xyz789",
        }
        
        sanitized = sanitize_log_data(data)
        
        assert sanitized["username"] == "john"
        assert sanitized["email"] == "john@example.com"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["user_token"] == "***REDACTED***"
    
    def test_validate_email_format_valid(self):
        """Accepte les emails valides."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
        ]
        
        for email in valid_emails:
            assert validate_email_format(email), f"{email} devrait être valide"
    
    def test_validate_email_format_invalid(self):
        """Rejette les emails invalides."""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user@domain",
            "",
        ]
        
        for email in invalid_emails:
            assert not validate_email_format(email), f"{email} devrait être invalide"
    
    def test_validate_password_strength_strong(self):
        """Accepte les mots de passe forts."""
        is_valid, errors = validate_password_strength("StrongPass123")
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_password_strength_weak(self):
        """Rejette les mots de passe faibles avec messages appropriés."""
        # Trop court
        is_valid, errors = validate_password_strength("Ab1")
        assert not is_valid
        assert any("8 caractères" in e for e in errors)
        
        # Pas de majuscule
        is_valid, errors = validate_password_strength("password123")
        assert not is_valid
        assert any("majuscule" in e for e in errors)
        
        # Pas de chiffre
        is_valid, errors = validate_password_strength("StrongPass")
        assert not is_valid
        assert any("chiffre" in e for e in errors)


class TestCorsConfiguration:
    """Tests pour la configuration CORS."""
    
    @patch.dict(os.environ, {"ALLOWED_ORIGINS": "*"})
    def test_cors_wildcard(self):
        """Retourne wildcard si configuré."""
        # Recharger la valeur
        from common import security
        import importlib
        importlib.reload(security)
        
        origins = security.get_cors_origins()
        assert "*" in origins
    
    @patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://localhost:3000,https://app.example.com"})
    def test_cors_specific_origins(self):
        """Retourne les origines spécifiques."""
        from common import security
        import importlib
        importlib.reload(security)
        
        origins = security.get_cors_origins()
        assert "http://localhost:3000" in origins
        assert "https://app.example.com" in origins
