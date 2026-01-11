"""
Tests d'intégration pour le module Auth.
Tests des routes API d'authentification.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =====================
# Setup de l'application
# =====================

@pytest.fixture
def app():
    """Crée une instance de l'application FastAPI pour les tests."""
    from fastapi import FastAPI
    from auth.routes import auth_api
    
    app = FastAPI()
    app.include_router(auth_api, prefix="/auth")
    return app


@pytest.fixture
def client(app):
    """Crée un client de test synchrone."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Crée un client de test asynchrone."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# =====================
# Tests des routes Auth
# =====================

class TestRegisterRoute:
    """Tests pour la route POST /auth/register."""

    def test_register_success(self, client, mock_collection, register_user_payload):
        """Vérifie l'enregistrement via l'API."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/register", json=register_user_payload)
            
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert data["role"] == "apprenti"

    def test_register_email_exists(self, client, mock_collection, register_user_payload):
        """Vérifie le rejet si l'email existe."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value={"email": "test@example.com"})
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/register", json=register_user_payload)
            
            assert response.status_code == 409

    def test_register_invalid_email(self, client, register_user_payload):
        """Vérifie le rejet pour un email invalide."""
        register_user_payload["email"] = "invalid-email"
        
        response = client.post("/auth/register", json=register_user_payload)
        
        assert response.status_code == 422  # Validation error

    def test_register_missing_field(self, client, register_user_payload):
        """Vérifie le rejet pour un champ manquant."""
        del register_user_payload["password"]
        
        response = client.post("/auth/register", json=register_user_payload)
        
        assert response.status_code == 422


class TestLoginRoute:
    """Tests pour la route POST /auth/login."""

    def test_login_success(self, client, mock_collection, sample_apprenti_data, login_payload):
        """Vérifie la connexion via l'API."""
        from auth.functions import hash_password
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("password123")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/login", json=login_payload)
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "me" in data

    def test_login_wrong_password(self, client, mock_collection, sample_apprenti_data, login_payload):
        """Vérifie le rejet pour mot de passe incorrect."""
        from auth.functions import hash_password
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("different_password")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/login", json=login_payload)
            
            assert response.status_code == 401

    def test_login_user_not_found(self, client, mock_collection, login_payload):
        """Vérifie le rejet pour utilisateur non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/login", json=login_payload)
            
            assert response.status_code == 404


class TestMeRoute:
    """Tests pour la route GET /auth/me."""

    def test_get_me_success(self, client, mock_collection, sample_apprenti_data, valid_token):
        """Vérifie la récupération du profil via l'API."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "me" in data

    def test_get_me_no_token(self, client):
        """Vérifie le rejet sans token."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Vérifie le rejet avec un token invalide."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401


class TestUpdateMeRoute:
    """Tests pour la route PATCH /auth/me."""

    def test_update_me_success(self, client, mock_collection, sample_apprenti_data, valid_token):
        """Vérifie la mise à jour du profil via l'API."""
        from auth.functions import hash_password
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("password123")
        updated_user = {**sample_apprenti_data, "email": "nouveau@example.com"}
        
        # Créer un mock qui gère les différents appels
        call_count = [0]
        
        def find_one_mock(query):
            async def _inner():
                nonlocal call_count
                call_count[0] += 1
                # Premier appel : récupérer utilisateur par email
                if call_count[0] == 1:
                    return sample_apprenti_data
                # Dernier appel : récupérer utilisateur mis à jour après update
                if "_id" in query:
                    return updated_user
                return None  # Email disponible
            return _inner()
        
        mock_collection.find_one = find_one_mock
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.patch(
                "/auth/me",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "email": "nouveau@example.com",
                    "current_password": "password123"
                }
            )
            
            assert response.status_code == 200


class TestUsersRoute:
    """Tests pour la route GET /auth/users."""

    def test_list_users(self, client, mock_collection, sample_apprenti_data, async_cursor_factory):
        """Vérifie la liste des utilisateurs via l'API."""
        import common.db as database
        
        cursor = async_cursor_factory([sample_apprenti_data])
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get("/auth/users")
            
            assert response.status_code == 200
            data = response.json()
            assert "users" in data


class TestGenerateEmailRoute:
    """Tests pour la route POST /auth/generate-email."""

    def test_generate_email_success(self, client, mock_collection):
        """Vérifie la génération d'email via l'API."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/generate-email", json={
                "nom": "Dupont",
                "prenom": "Jean",
                "profil": "apprenti"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            assert "password" in data
            assert "jean.dupont@reseaualternance.fr" == data["email"]


class TestRecoverPasswordRoute:
    """Tests pour la route POST /auth/recover-password."""

    def test_recover_password_success(self, client, mock_collection, sample_apprenti_data):
        """Vérifie la récupération de mot de passe via l'API."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/recover-password", json={
                "email": "jean.dupont@reseaualternance.fr",
                "profil": "apprenti"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "new_password" in data

    def test_recover_password_user_not_found(self, client, mock_collection):
        """Vérifie le rejet si l'utilisateur n'existe pas."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/recover-password", json={
                "email": "nonexistent@example.com",
                "profil": "apprenti"
            })
            
            assert response.status_code == 404


class TestRegisterEntityRoute:
    """Tests pour la route POST /auth/register-entity."""

    def test_register_entity_success(self, client, mock_collection):
        """Vérifie l'enregistrement d'entité via l'API."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/register-entity", json={
                "raisonSociale": "TechCorp",
                "siret": "12345678900011",
                "email": "contact@techcorp.fr",
                "role": "entreprise"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "entity_id" in data


# =====================
# Tests de validation des payloads
# =====================

class TestPayloadValidation:
    """Tests de validation des données d'entrée."""

    def test_register_invalid_role(self, client):
        """Vérifie le rejet pour un rôle invalide."""
        response = client.post("/auth/register", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "+33600000000",
            "age": 25,
            "annee_academique": "E5a",
            "password": "SecurePassword123",
            "role": "invalid_role"
        })
        
        assert response.status_code == 422

    def test_login_empty_email(self, client):
        """Vérifie le rejet pour un email vide."""
        response = client.post("/auth/login", json={
            "email": "",
            "password": "password123"
        })
        
        assert response.status_code == 422

    def test_generate_email_missing_profil(self, client):
        """Vérifie le rejet pour un profil manquant."""
        response = client.post("/auth/generate-email", json={
            "nom": "Dupont",
            "prenom": "Jean"
        })
        
        assert response.status_code == 422


# =====================
# Tests de sécurité
# =====================

class TestSecurityFeatures:
    """Tests des fonctionnalités de sécurité."""

    def test_password_not_returned(self, client, mock_collection, sample_apprenti_data):
        """Vérifie que le mot de passe n'est jamais retourné."""
        from auth.functions import hash_password
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("password123")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/login", json={
                "email": "jean.dupont@reseaualternance.fr",
                "password": "password123"
            })
            
            data = response.json()
            assert "password" not in str(data)
            assert "hashed_password" not in str(data)

    def test_token_expiration_included(self, client, mock_collection, sample_apprenti_data):
        """Vérifie que le token inclut une expiration."""
        from auth.functions import hash_password, decode_access_token
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("password123")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/auth/login", json={
                "email": "jean.dupont@reseaualternance.fr",
                "password": "password123"
            })
            
            token = response.json()["access_token"]
            decoded = decode_access_token(token)
            
            assert "exp" in decoded

    def test_expired_token_rejected(self, client, expired_token):
        """Vérifie que les tokens expirés sont rejetés."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401