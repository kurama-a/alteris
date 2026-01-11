"""
Tests pour le module Coordonatrice.
Tests de gestion des coordinatrices de formation.
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
# Setup de l'application
# =====================

@pytest.fixture
def app():
    """Crée une instance de l'application Coordonatrice."""
    from fastapi import FastAPI
    from coordonatrice.routes import coordonatrice_api
    
    app = FastAPI()
    app.include_router(coordonatrice_api, prefix="/coordonatrice")
    return app


@pytest.fixture
def client(app):
    """Client pour l'API Coordonatrice."""
    return TestClient(app)


# =====================
# Fixtures spécifiques
# =====================

@pytest.fixture
def sample_coordonatrice_data():
    """Données d'une coordonatrice de test."""
    return {
        "_id": ObjectId(),
        "first_name": "Sophie",
        "last_name": "Durand",
        "email": "sophie.durand@esgi.fr",
        "phone": "+33612345678",
        "role": "coordonatrice"
    }


# =====================
# Tests des routes Health
# =====================

class TestCoordonatriceHealth:
    """Tests pour la route health de coordonatrice."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/coordonatrice/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "coordonatrice"


class TestCoordonatriceProfile:
    """Tests pour le profil coordonatrice."""

    def test_get_profile(self, client):
        """Vérifie la route profil."""
        response = client.get("/coordonatrice/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Données du profil coordonatrice"


# =====================
# Tests des modèles
# =====================

class TestCoordonatriceModels:
    """Tests pour les modèles Coordonatrice."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from coordonatrice.models import HealthResponse
        
        response = HealthResponse(status="ok", service="coordonatrice")
        
        assert response.status == "ok"
        assert response.service == "coordonatrice"

    def test_user_model(self):
        """Vérifie le modèle User."""
        from coordonatrice.models import User
        
        user = User(
            first_name="Sophie",
            last_name="Durand",
            email="sophie.durand@esgi.fr",
            phone="+33612345678",
            role="coordonatrice"
        )
        
        assert user.first_name == "Sophie"
        assert user.email == "sophie.durand@esgi.fr"

    def test_user_update_model(self):
        """Vérifie le modèle UserUpdate."""
        from coordonatrice.models import UserUpdate
        
        update = UserUpdate(
            first_name="Sophie",
            phone="+33698765432"
        )
        
        assert update.first_name == "Sophie"
        assert update.phone == "+33698765432"


# =====================
# Tests des fonctions unitaires
# =====================

class TestGetCollection:
    """Tests pour la fonction get_collection."""

    def test_get_collection_success(self, mock_collection):
        """Vérifie la récupération de la collection."""
        import common.db as database
        from coordonatrice.functions import get_collection
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = get_collection()
            
            mock_db.__getitem__.assert_called_with("users_coordonatrice")

    def test_get_collection_db_not_initialized(self):
        """Vérifie le rejet si DB non initialisée."""
        import common.db as database
        from coordonatrice.functions import get_collection
        
        with patch.object(database, 'db', None):
            with pytest.raises(HTTPException) as exc_info:
                get_collection()
            
            assert exc_info.value.status_code == 500
            assert "DB" in exc_info.value.detail


class TestSerialize:
    """Tests pour la fonction serialize."""

    def test_serialize_document(self, sample_coordonatrice_data):
        """Vérifie la sérialisation d'un document."""
        from coordonatrice.functions import serialize
        
        result = serialize(sample_coordonatrice_data)
        
        assert result["_id"] == str(sample_coordonatrice_data["_id"])
        assert result["first_name"] == "Sophie"
        assert result["last_name"] == "Durand"
        assert result["email"] == "sophie.durand@esgi.fr"
        assert result["role"] == "coordonatrice"

    def test_serialize_none_returns_none(self):
        """Vérifie que None retourne None."""
        from coordonatrice.functions import serialize
        
        result = serialize(None)
        
        assert result is None


# =====================
# Tests de création
# =====================

class TestCreerCoordonatrice:
    """Tests pour la création de coordonatrice."""

    @pytest.mark.asyncio
    async def test_creer_coordonatrice_success(self, sample_coordonatrice_data, mock_collection):
        """Vérifie la création réussie."""
        import common.db as database
        from coordonatrice.functions import creer_coordonatrice
        from coordonatrice.models import User
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_coordonatrice_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_coordonatrice_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = User(
                first_name="Sophie",
                last_name="Durand",
                email="sophie.durand@esgi.fr",
                phone="+33612345678"
            )
            
            result = await creer_coordonatrice(payload)
            
            assert result["message"] == "Coordonatrice créée"
            assert result["data"]["first_name"] == "Sophie"


class TestCreerCoordonatriceRoute:
    """Tests d'intégration pour la route de création."""

    def test_create_coordonatrice_route(self, client, sample_coordonatrice_data, mock_collection):
        """Vérifie la route de création."""
        import common.db as database
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_coordonatrice_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_coordonatrice_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/coordonatrice/", json={
                "first_name": "Sophie",
                "last_name": "Durand",
                "email": "sophie.durand@esgi.fr",
                "phone": "+33612345678"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Coordonatrice créée"


# =====================
# Tests de mise à jour
# =====================

class TestMettreAJourCoordonatrice:
    """Tests pour la mise à jour de coordonatrice."""

    @pytest.mark.asyncio
    async def test_update_coordonatrice_success(self, sample_coordonatrice_data, mock_collection):
        """Vérifie la mise à jour réussie."""
        import common.db as database
        from coordonatrice.functions import mettre_a_jour_coordonatrice
        from coordonatrice.models import UserUpdate
        
        updated_data = sample_coordonatrice_data.copy()
        updated_data["phone"] = "+33698765432"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UserUpdate(phone="+33698765432")
            result = await mettre_a_jour_coordonatrice(
                str(sample_coordonatrice_data["_id"]),
                payload
            )
            
            assert result["message"] == "Coordonatrice mise à jour"

    @pytest.mark.asyncio
    async def test_update_coordonatrice_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvée."""
        import common.db as database
        from coordonatrice.functions import mettre_a_jour_coordonatrice
        from coordonatrice.models import UserUpdate
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UserUpdate(phone="+33698765432")
            
            with pytest.raises(HTTPException) as exc_info:
                await mettre_a_jour_coordonatrice(str(ObjectId()), payload)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_coordonatrice_empty_payload(self, mock_collection):
        """Vérifie le rejet si payload vide."""
        import common.db as database
        from coordonatrice.functions import mettre_a_jour_coordonatrice
        from coordonatrice.models import UserUpdate
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            # Payload sans données
            payload = UserUpdate()
            
            with pytest.raises(HTTPException) as exc_info:
                await mettre_a_jour_coordonatrice(str(ObjectId()), payload)
            
            assert exc_info.value.status_code == 400


class TestMettreAJourCoordonatriceRoute:
    """Tests d'intégration pour la route de mise à jour."""

    def test_update_coordonatrice_route(self, client, sample_coordonatrice_data, mock_collection):
        """Vérifie la route de mise à jour."""
        import common.db as database
        
        updated_data = sample_coordonatrice_data.copy()
        updated_data["phone"] = "+33698765432"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/coordonatrice/{sample_coordonatrice_data['_id']}",
                json={"phone": "+33698765432"}
            )
            
            assert response.status_code == 200


# =====================
# Tests de suppression
# =====================

class TestSupprimerCoordonatrice:
    """Tests pour la suppression de coordonatrice."""

    @pytest.mark.asyncio
    async def test_supprimer_coordonatrice_success(self, sample_coordonatrice_data, mock_collection):
        """Vérifie la suppression réussie."""
        import common.db as database
        from coordonatrice.functions import supprimer_coordonatrice
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await supprimer_coordonatrice(str(sample_coordonatrice_data["_id"]))
            
            assert result["message"] == "Coordonatrice supprimée"
            assert result["coordonatrice_id"] == str(sample_coordonatrice_data["_id"])

    @pytest.mark.asyncio
    async def test_supprimer_coordonatrice_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvée."""
        import common.db as database
        from coordonatrice.functions import supprimer_coordonatrice
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await supprimer_coordonatrice(str(ObjectId()))
            
            assert exc_info.value.status_code == 404


class TestSupprimerCoordonatriceRoute:
    """Tests d'intégration pour la route de suppression."""

    def test_delete_coordonatrice_route(self, client, sample_coordonatrice_data, mock_collection):
        """Vérifie la route de suppression."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/coordonatrice/{sample_coordonatrice_data['_id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Coordonatrice supprimée"

    def test_delete_coordonatrice_not_found_route(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/coordonatrice/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de validation
# =====================

class TestCoordonatricePayloadValidation:
    """Tests de validation des payloads coordonatrice."""

    def test_create_missing_email(self, client):
        """Vérifie le rejet sans email."""
        response = client.post("/coordonatrice/", json={
            "first_name": "Sophie",
            "last_name": "Durand"
        })
        
        assert response.status_code == 422

    def test_create_invalid_email(self, client):
        """Vérifie le rejet pour email invalide."""
        response = client.post("/coordonatrice/", json={
            "first_name": "Sophie",
            "last_name": "Durand",
            "email": "invalid-email"
        })
        
        assert response.status_code == 422