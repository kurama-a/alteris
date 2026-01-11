"""
Tests pour le module Responsable Cursus.
Tests de gestion des responsables de cursus.
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
    """Crée une instance de l'application Responsable Cursus."""
    from fastapi import FastAPI
    from responsable_cursus.routes import responsable_cursus_api
    
    app = FastAPI()
    app.include_router(responsable_cursus_api, prefix="/responsable-cursus")
    return app


@pytest.fixture
def client(app):
    """Client pour l'API Responsable Cursus."""
    return TestClient(app)


# =====================
# Fixtures spécifiques
# =====================

@pytest.fixture
def sample_responsable_cursus_data():
    """Données d'un responsable cursus de test."""
    return {
        "_id": ObjectId(),
        "first_name": "Laurent",
        "last_name": "Moreau",
        "email": "laurent.moreau@esgi.fr",
        "phone": "+33612345678",
        "role": "responsable_cursus"
    }


# =====================
# Tests des routes Health
# =====================

class TestResponsableCursusHealth:
    """Tests pour la route health du responsable cursus."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/responsable-cursus/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "responsable_cursus"


# =====================
# Tests des modèles
# =====================

class TestResponsableCursusModels:
    """Tests pour les modèles Responsable Cursus."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from responsable_cursus.models import HealthResponse
        
        response = HealthResponse(status="ok", service="responsable_cursus")
        
        assert response.status == "ok"
        assert response.service == "responsable_cursus"

    def test_user_model(self):
        """Vérifie le modèle User."""
        from responsable_cursus.models import User
        
        user = User(
            first_name="Laurent",
            last_name="Moreau",
            email="laurent.moreau@esgi.fr",
            phone="+33612345678",
            role="responsable_cursus"
        )
        
        assert user.first_name == "Laurent"
        assert user.email == "laurent.moreau@esgi.fr"

    def test_user_update_model(self):
        """Vérifie le modèle UserUpdate."""
        from responsable_cursus.models import UserUpdate
        
        update = UserUpdate(
            first_name="Laurent",
            phone="+33698765432"
        )
        
        assert update.first_name == "Laurent"
        assert update.phone == "+33698765432"


# =====================
# Tests des fonctions unitaires
# =====================

class TestGetCollection:
    """Tests pour la fonction get_collection."""

    def test_get_collection_success(self, mock_collection):
        """Vérifie la récupération de la collection."""
        import common.db as database
        from responsable_cursus.functions import get_collection
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = get_collection()
            
            mock_db.__getitem__.assert_called_with("users_responsable_cursus")

    def test_get_collection_db_not_initialized(self):
        """Vérifie le rejet si DB non initialisée."""
        import common.db as database
        from responsable_cursus.functions import get_collection
        
        with patch.object(database, 'db', None):
            with pytest.raises(HTTPException) as exc_info:
                get_collection()
            
            assert exc_info.value.status_code == 500
            assert "DB" in exc_info.value.detail


class TestSerialize:
    """Tests pour la fonction serialize."""

    def test_serialize_document(self, sample_responsable_cursus_data):
        """Vérifie la sérialisation d'un document."""
        from responsable_cursus.functions import serialize
        
        result = serialize(sample_responsable_cursus_data)
        
        assert result["_id"] == str(sample_responsable_cursus_data["_id"])
        assert result["first_name"] == "Laurent"
        assert result["last_name"] == "Moreau"
        assert result["email"] == "laurent.moreau@esgi.fr"
        assert result["role"] == "responsable_cursus"

    def test_serialize_none_returns_none(self):
        """Vérifie que None retourne None."""
        from responsable_cursus.functions import serialize
        
        result = serialize(None)
        
        assert result is None


# =====================
# Tests de récupération des infos complètes
# =====================

class TestRecupererInfosResponsableCursusCompletes:
    """Tests pour la récupération des infos complètes."""

    @pytest.mark.asyncio
    async def test_recuperer_infos_success(self, sample_responsable_cursus_data, mock_collection):
        """Vérifie la récupération réussie."""
        import common.db as database
        from responsable_cursus.functions import recuperer_infos_responsable_cursus_completes
        
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_cursus_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await recuperer_infos_responsable_cursus_completes(
                str(sample_responsable_cursus_data["_id"])
            )
            
            assert result["message"] == "Données récupérées avec succès"
            assert result["data"]["first_name"] == "Laurent"

    @pytest.mark.asyncio
    async def test_recuperer_infos_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvé."""
        import common.db as database
        from responsable_cursus.functions import recuperer_infos_responsable_cursus_completes
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await recuperer_infos_responsable_cursus_completes(str(ObjectId()))
            
            assert exc_info.value.status_code == 404


class TestRecupererInfosResponsableCursusCompletesRoute:
    """Tests d'intégration pour la route infos complètes."""

    def test_get_infos_completes_route(
        self, client, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la route infos complètes."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_cursus_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(
                f"/responsable-cursus/infos-completes/{sample_responsable_cursus_data['_id']}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Données récupérées avec succès"

    def test_get_infos_completes_not_found(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/responsable-cursus/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de création
# =====================

class TestCreerResponsableCursus:
    """Tests pour la création de responsable cursus."""

    @pytest.mark.asyncio
    async def test_creer_responsable_cursus_success(
        self, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la création réussie."""
        import common.db as database
        from responsable_cursus.functions import creer_responsable_cursus
        from responsable_cursus.models import User
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_responsable_cursus_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_cursus_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = User(
                first_name="Laurent",
                last_name="Moreau",
                email="laurent.moreau@esgi.fr",
                phone="+33612345678"
            )
            
            result = await creer_responsable_cursus(payload)
            
            assert result["message"] == "Responsable cursus créé"
            assert result["data"]["first_name"] == "Laurent"


class TestCreerResponsableCursusRoute:
    """Tests d'intégration pour la route de création."""

    def test_create_responsable_cursus_route(
        self, client, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la route de création."""
        import common.db as database
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_responsable_cursus_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_responsable_cursus_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/responsable-cursus/", json={
                "first_name": "Laurent",
                "last_name": "Moreau",
                "email": "laurent.moreau@esgi.fr",
                "phone": "+33612345678"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Responsable cursus créé"


# =====================
# Tests de mise à jour
# =====================

class TestMettreAJourResponsableCursus:
    """Tests pour la mise à jour de responsable cursus."""

    @pytest.mark.asyncio
    async def test_update_responsable_cursus_success(
        self, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la mise à jour réussie."""
        import common.db as database
        from responsable_cursus.functions import mettre_a_jour_responsable_cursus
        from responsable_cursus.models import UserUpdate
        
        updated_data = sample_responsable_cursus_data.copy()
        updated_data["phone"] = "+33698765432"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UserUpdate(phone="+33698765432")
            result = await mettre_a_jour_responsable_cursus(
                str(sample_responsable_cursus_data["_id"]),
                payload
            )
            
            assert result["message"] == "Responsable cursus mis à jour"

    @pytest.mark.asyncio
    async def test_update_responsable_cursus_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvé."""
        import common.db as database
        from responsable_cursus.functions import mettre_a_jour_responsable_cursus
        from responsable_cursus.models import UserUpdate
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UserUpdate(phone="+33698765432")
            
            with pytest.raises(HTTPException) as exc_info:
                await mettre_a_jour_responsable_cursus(str(ObjectId()), payload)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_responsable_cursus_empty_payload(self, mock_collection):
        """Vérifie le rejet si payload vide."""
        import common.db as database
        from responsable_cursus.functions import mettre_a_jour_responsable_cursus
        from responsable_cursus.models import UserUpdate
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UserUpdate()
            
            with pytest.raises(HTTPException) as exc_info:
                await mettre_a_jour_responsable_cursus(str(ObjectId()), payload)
            
            assert exc_info.value.status_code == 400


class TestMettreAJourResponsableCursusRoute:
    """Tests d'intégration pour la route de mise à jour."""

    def test_update_responsable_cursus_route(
        self, client, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la route de mise à jour."""
        import common.db as database
        
        updated_data = sample_responsable_cursus_data.copy()
        updated_data["phone"] = "+33698765432"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/responsable-cursus/{sample_responsable_cursus_data['_id']}",
                json={"phone": "+33698765432"}
            )
            
            assert response.status_code == 200


# =====================
# Tests de suppression
# =====================

class TestSupprimerResponsableCursus:
    """Tests pour la suppression de responsable cursus."""

    @pytest.mark.asyncio
    async def test_supprimer_responsable_cursus_success(
        self, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la suppression réussie."""
        import common.db as database
        from responsable_cursus.functions import supprimer_responsable_cursus
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await supprimer_responsable_cursus(
                str(sample_responsable_cursus_data["_id"])
            )
            
            assert result["message"] == "Responsable cursus supprimé"
            assert result["responsable_cursus_id"] == str(sample_responsable_cursus_data["_id"])

    @pytest.mark.asyncio
    async def test_supprimer_responsable_cursus_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvé."""
        import common.db as database
        from responsable_cursus.functions import supprimer_responsable_cursus
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await supprimer_responsable_cursus(str(ObjectId()))
            
            assert exc_info.value.status_code == 404


class TestSupprimerResponsableCursusRoute:
    """Tests d'intégration pour la route de suppression."""

    def test_delete_responsable_cursus_route(
        self, client, sample_responsable_cursus_data, mock_collection
    ):
        """Vérifie la route de suppression."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(
                f"/responsable-cursus/{sample_responsable_cursus_data['_id']}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Responsable cursus supprimé"

    def test_delete_responsable_cursus_not_found_route(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/responsable-cursus/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de validation
# =====================

class TestResponsableCursusPayloadValidation:
    """Tests de validation des payloads responsable cursus."""

    def test_create_missing_email(self, client):
        """Vérifie le rejet sans email."""
        response = client.post("/responsable-cursus/", json={
            "first_name": "Laurent",
            "last_name": "Moreau"
        })
        
        assert response.status_code == 422

    def test_create_invalid_email(self, client):
        """Vérifie le rejet pour email invalide."""
        response = client.post("/responsable-cursus/", json={
            "first_name": "Laurent",
            "last_name": "Moreau",
            "email": "invalid-email"
        })
        
        assert response.status_code == 422