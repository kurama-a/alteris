"""
Tests pour les modules Tuteur, Maître d'apprentissage et Professeur.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =====================
# Setup des applications
# =====================

@pytest.fixture
def tuteur_app():
    """Crée une instance de l'application Tuteur."""
    from fastapi import FastAPI
    from tuteur.routes import tuteur_api
    
    app = FastAPI()
    app.include_router(tuteur_api, prefix="/tuteur")
    return app


@pytest.fixture
def tuteur_client(tuteur_app):
    """Client pour l'API Tuteur."""
    return TestClient(tuteur_app)


@pytest.fixture
def maitre_app():
    """Crée une instance de l'application Maître."""
    from fastapi import FastAPI
    from maitre.routes import maitre_api
    
    app = FastAPI()
    app.include_router(maitre_api, prefix="/maitre")
    return app


@pytest.fixture
def maitre_client(maitre_app):
    """Client pour l'API Maître."""
    return TestClient(maitre_app)


@pytest.fixture
def professeur_app():
    """Crée une instance de l'application Professeur."""
    from fastapi import FastAPI
    from professeur.routes import professeur_api
    
    app = FastAPI()
    app.include_router(professeur_api, prefix="/professeur")
    return app


@pytest.fixture
def professeur_client(professeur_app):
    """Client pour l'API Professeur."""
    return TestClient(professeur_app)


# =====================
# Tests Tuteur
# =====================

class TestTuteurHealth:
    """Tests pour la route health du tuteur."""

    def test_health_returns_ok(self, tuteur_client):
        """Vérifie que la route health retourne OK."""
        response = tuteur_client.get("/tuteur/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "tuteur"


class TestTuteurProfile:
    """Tests pour le profil tuteur."""

    def test_get_profile(self, tuteur_client):
        """Vérifie la route profil."""
        response = tuteur_client.get("/tuteur/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestTuteurInfosCompletes:
    """Tests pour les infos complètes du tuteur."""

    def test_get_infos_completes_success(
        self, tuteur_client, sample_tuteur_data, mock_collection, sample_object_ids
    ):
        """Vérifie la récupération des infos tuteur."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_tuteur_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = tuteur_client.get(f"/tuteur/infos-completes/{sample_object_ids['tuteur']}")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert data["data"]["first_name"] == "Marie"

    def test_get_infos_completes_not_found(self, tuteur_client, mock_collection):
        """Vérifie le rejet si tuteur non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = tuteur_client.get(f"/tuteur/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests Maître d'apprentissage
# =====================

class TestMaitreHealth:
    """Tests pour la route health du maître."""

    def test_health_returns_ok(self, maitre_client):
        """Vérifie que la route health retourne OK."""
        response = maitre_client.get("/maitre/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "maitre_apprentissage"


class TestMaitreProfile:
    """Tests pour le profil maître."""

    def test_get_profile(self, maitre_client):
        """Vérifie la route profil."""
        response = maitre_client.get("/maitre/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestMaitreInfosCompletes:
    """Tests pour les infos complètes du maître."""

    def test_get_infos_completes_success(
        self, maitre_client, sample_maitre_data, mock_collection, sample_object_ids
    ):
        """Vérifie la récupération des infos maître."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_maitre_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = maitre_client.get(f"/maitre/infos-completes/{sample_object_ids['maitre']}")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert data["data"]["first_name"] == "Pierre"

    def test_get_infos_completes_not_found(self, maitre_client, mock_collection):
        """Vérifie le rejet si maître non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = maitre_client.get(f"/maitre/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests Professeur
# =====================

class TestProfesseurHealth:
    """Tests pour la route health du professeur."""

    def test_health_returns_ok(self, professeur_client):
        """Vérifie que la route health retourne OK."""
        response = professeur_client.get("/professeur/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "professeur"


class TestProfesseurProfile:
    """Tests pour le profil professeur."""

    def test_get_profile(self, professeur_client):
        """Vérifie la route profil."""
        response = professeur_client.get("/professeur/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestProfesseurInfosCompletes:
    """Tests pour les infos complètes du professeur."""

    def test_get_infos_completes_success(
        self, professeur_client, sample_professeur_data, mock_collection, sample_object_ids
    ):
        """Vérifie la récupération des infos professeur."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_professeur_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = professeur_client.get(f"/professeur/infos-completes/{sample_object_ids['professeur']}")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert data["data"]["first_name"] == "Sophie"

    def test_get_infos_completes_not_found(self, professeur_client, mock_collection):
        """Vérifie le rejet si professeur non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = professeur_client.get(f"/professeur/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests des modèles
# =====================

class TestTuteurModels:
    """Tests pour les modèles Tuteur."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from tuteur.models import HealthResponse
        
        response = HealthResponse(status="ok", service="tuteur")
        
        assert response.status == "ok"
        assert response.service == "tuteur"

    def test_user_model(self):
        """Vérifie le modèle User."""
        from tuteur.models import User
        
        user = User(
            name="Marie Martin",
            email="marie@example.com",
            age=35
        )
        
        assert user.name == "Marie Martin"
        assert user.email == "marie@example.com"
        assert user.age == 35


class TestMaitreModels:
    """Tests pour les modèles Maître."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from maitre.models import HealthResponse
        
        response = HealthResponse(status="ok", service="maitre_apprentissage")
        
        assert response.status == "ok"
        assert response.service == "maitre_apprentissage"


class TestProfesseurModels:
    """Tests pour les modèles Professeur."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from professeur.models import HealthResponse
        
        response = HealthResponse(status="ok", service="professeur")
        
        assert response.status == "ok"
        assert response.service == "professeur"


# =====================
# Tests de DB non initialisée
# =====================

class TestDBNotInitialized:
    """Tests pour les cas où la DB n'est pas initialisée."""

    def test_tuteur_db_not_initialized(self, tuteur_client, sample_object_ids):
        """Vérifie le comportement tuteur sans DB."""
        import common.db as database
        
        with patch.object(database, 'db', None):
            response = tuteur_client.get(f"/tuteur/infos-completes/{sample_object_ids['tuteur']}")
            
            assert response.status_code == 500

    def test_maitre_db_not_initialized(self, maitre_client, sample_object_ids):
        """Vérifie le comportement maître sans DB."""
        import common.db as database
        
        with patch.object(database, 'db', None):
            response = maitre_client.get(f"/maitre/infos-completes/{sample_object_ids['maitre']}")
            
            assert response.status_code == 500

    def test_professeur_db_not_initialized(self, professeur_client, sample_object_ids):
        """Vérifie le comportement professeur sans DB."""
        import common.db as database
        
        with patch.object(database, 'db', None):
            response = professeur_client.get(f"/professeur/infos-completes/{sample_object_ids['professeur']}")
            
            assert response.status_code == 500