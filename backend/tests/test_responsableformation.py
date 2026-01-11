"""
Tests pour le module Responsable Formation.
Tests de gestion des responsables de formation.
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
    """Crée une instance de l'application Responsable Formation."""
    from fastapi import FastAPI
    from responsableformation.routes import responsableformation_api
    
    app = FastAPI()
    app.include_router(responsableformation_api, prefix="/responsable-formation")
    return app


@pytest.fixture
def client(app):
    """Client pour l'API Responsable Formation."""
    return TestClient(app)


# =====================
# Fixtures spécifiques
# =====================

@pytest.fixture
def sample_responsable_formation_data():
    """Données d'un responsable formation de test."""
    return {
        "_id": ObjectId(),
        "first_name": "Claire",
        "last_name": "Dubois",
        "email": "claire.dubois@esgi.fr",
        "phone": "+33612345678",
        "role": "responsable_formation"
    }


# =====================
# Tests des routes Health
# =====================

class TestResponsableFormationHealth:
    """Tests pour la route health du responsable formation."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/responsable-formation/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "responsable_formation"


class TestResponsableFormationProfile:
    """Tests pour le profil responsable formation."""

    def test_get_profile(self, client):
        """Vérifie la route profil."""
        response = client.get("/responsable-formation/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Données du profil responsable de formation"


# =====================
# Tests des modèles
# =====================

class TestResponsableFormationModels:
    """Tests pour les modèles Responsable Formation."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from responsableformation.models import HealthResponse
        
        response = HealthResponse(status="ok", service="responsable_formation")
        
        assert response.status == "ok"
        assert response.service == "responsable_formation"

    def test_user_model(self):
        """Vérifie le modèle User."""
        from responsableformation.models import User
        
        user = User(
            first_name="Claire",
            last_name="Dubois",
            email="claire.dubois@esgi.fr",
            phone="+33612345678",
            role="responsable_formation"
        )
        
        assert user.first_name == "Claire"
        assert user.email == "claire.dubois@esgi.fr"

    def test_user_update_model(self):
        """Vérifie le modèle UserUpdate."""
        from responsableformation.models import UserUpdate
        
        update = UserUpdate(
            first_name="Claire",
            phone="+33698765432"
        )
        
        assert update.first_name == "Claire"
        assert update.phone == "+33698765432"


# =====================
# Tests de récupération des infos complètes
# =====================

class TestRecupererInfosResponsableFormationCompletes:
    """Tests pour la récupération des infos complètes."""

    def test_get_infos_completes_route(
        self, client, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la route infos complètes."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_formation_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(
                f"/responsable-formation/infos-completes/{sample_responsable_formation_data['_id']}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Données récupérées avec succès"
            assert data["data"]["first_name"] == "Claire"

    def test_get_infos_completes_not_found(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/responsable-formation/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404

    def test_get_infos_completes_db_not_initialized(self, client):
        """Vérifie le rejet 500 si DB non initialisée."""
        import common.db as database
        
        with patch.object(database, 'db', None):
            response = client.get(f"/responsable-formation/infos-completes/{ObjectId()}")
            
            assert response.status_code == 500


# =====================
# Tests de création
# =====================

class TestCreerResponsableFormation:
    """Tests pour la création de responsable formation."""

    def test_create_responsable_formation_route(
        self, client, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la route de création."""
        import common.db as database
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_responsable_formation_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_formation_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/responsable-formation/", json={
                "first_name": "Claire",
                "last_name": "Dubois",
                "email": "claire.dubois@esgi.fr",
                "phone": "+33612345678"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Responsable formation créé"


# =====================
# Tests de mise à jour
# =====================

class TestMettreAJourResponsableFormation:
    """Tests pour la mise à jour de responsable formation."""

    def test_update_responsable_formation_route(
        self, client, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la route de mise à jour."""
        import common.db as database
        
        updated_data = sample_responsable_formation_data.copy()
        updated_data["phone"] = "+33698765432"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/responsable-formation/{sample_responsable_formation_data['_id']}",
                json={"phone": "+33698765432"}
            )
            
            assert response.status_code == 200

    def test_update_responsable_formation_not_found(self, client, mock_collection):
        """Vérifie le rejet 404 si non trouvé."""
        import common.db as database
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/responsable-formation/{ObjectId()}",
                json={"phone": "+33698765432"}
            )
            
            assert response.status_code == 404


# =====================
# Tests de suppression
# =====================

class TestSupprimerResponsableFormation:
    """Tests pour la suppression de responsable formation."""

    def test_delete_responsable_formation_route(
        self, client, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la route de suppression."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(
                f"/responsable-formation/{sample_responsable_formation_data['_id']}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Responsable formation supprimé"

    def test_delete_responsable_formation_not_found_route(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/responsable-formation/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de validation
# =====================

class TestResponsableFormationPayloadValidation:
    """Tests de validation des payloads responsable formation."""

    def test_create_missing_email(self, client):
        """Vérifie le rejet sans email."""
        response = client.post("/responsable-formation/", json={
            "first_name": "Claire",
            "last_name": "Dubois"
        })
        
        assert response.status_code == 422

    def test_create_invalid_email(self, client):
        """Vérifie le rejet pour email invalide."""
        response = client.post("/responsable-formation/", json={
            "first_name": "Claire",
            "last_name": "Dubois",
            "email": "invalid-email"
        })
        
        assert response.status_code == 422


# =====================
# Tests des fonctions
# =====================

class TestResponsableFormationFunctions:
    """Tests pour les fonctions du module responsable formation."""

    @pytest.mark.asyncio
    async def test_creer_responsable_formation(
        self, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la fonction creer_responsable_formation."""
        import common.db as database
        from responsableformation.functions import creer_responsable_formation
        from responsableformation.models import User
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_responsable_formation_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_formation_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = User(
                first_name="Claire",
                last_name="Dubois",
                email="claire.dubois@esgi.fr",
                phone="+33612345678"
            )
            
            result = await creer_responsable_formation(payload)
            
            assert result["message"] == "Responsable formation créé"
            assert result["data"]["first_name"] == "Claire"

    @pytest.mark.asyncio
    async def test_supprimer_responsable_formation(
        self, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la fonction supprimer_responsable_formation."""
        import common.db as database
        from responsableformation.functions import supprimer_responsable_formation
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await supprimer_responsable_formation(
                str(sample_responsable_formation_data["_id"])
            )
            
            assert result["message"] == "Responsable formation supprimé"
            assert result["responsableformation_id"] == str(sample_responsable_formation_data["_id"])

    @pytest.mark.asyncio
    async def test_supprimer_responsable_formation_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvé."""
        import common.db as database
        from responsableformation.functions import supprimer_responsable_formation
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await supprimer_responsable_formation(str(ObjectId()))
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_mettre_a_jour_responsable_formation(
        self, sample_responsable_formation_data, mock_collection
    ):
        """Vérifie la fonction mettre_a_jour_responsable_formation."""
        import common.db as database
        from responsableformation.functions import mettre_a_jour_responsable_formation
        from responsableformation.models import UserUpdate
        
        updated_data = sample_responsable_formation_data.copy()
        updated_data["phone"] = "+33698765432"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UserUpdate(phone="+33698765432")
            result = await mettre_a_jour_responsable_formation(
                str(sample_responsable_formation_data["_id"]),
                payload
            )
            
            assert result["message"] == "Responsable formation mis à jour"
            assert result["data"]["phone"] == "+33698765432"
