"""
Tests pour le module Entreprise.
Tests de gestion des entreprises partenaires.
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
    """Crée une instance de l'application Entreprise."""
    from fastapi import FastAPI
    from entreprise.routes import entreprise_api
    
    app = FastAPI()
    app.include_router(entreprise_api, prefix="/entreprise")
    return app


@pytest.fixture
def client(app):
    """Client pour l'API Entreprise."""
    return TestClient(app)


# =====================
# Fixtures spécifiques
# =====================

@pytest.fixture
def sample_entreprise_data():
    """Données d'une entreprise de test."""
    return {
        "_id": ObjectId(),
        "raisonSociale": "Tech Solutions SA",
        "siret": "12345678901234",
        "adresse": "10 Avenue des Champs, 75008 Paris",
        "email": "contact@techsolutions.fr",
        "creeLe": datetime.utcnow().isoformat(),
        "role": "entreprise"
    }


# =====================
# Tests des routes Health
# =====================

class TestEntrepriseHealth:
    """Tests pour la route health de l'entreprise."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/entreprise/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "entreprise"


# =====================
# Tests des modèles
# =====================

class TestEntrepriseModels:
    """Tests pour les modèles Entreprise."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from entreprise.models import HealthResponse
        
        response = HealthResponse(status="ok", service="entreprise")
        
        assert response.status == "ok"
        assert response.service == "entreprise"

    def test_entity_model(self):
        """Vérifie le modèle Entity."""
        from entreprise.models import Entity
        
        entity = Entity(
            raisonSociale="Tech Solutions SA",
            siret="12345678901234",
            adresse="10 Avenue des Champs, 75008 Paris",
            email="contact@techsolutions.fr"
        )
        
        assert entity.raisonSociale == "Tech Solutions SA"
        assert entity.siret == "12345678901234"

    def test_entity_update_model(self):
        """Vérifie le modèle EntityUpdate."""
        from entreprise.models import EntityUpdate
        
        update = EntityUpdate(
            raisonSociale="Tech Solutions SAS",
            adresse="12 Avenue des Champs, 75008 Paris"
        )
        
        assert update.raisonSociale == "Tech Solutions SAS"
        assert update.adresse == "12 Avenue des Champs, 75008 Paris"


# =====================
# Tests des fonctions unitaires
# =====================

class TestGetCollection:
    """Tests pour la fonction get_collection."""

    def test_get_collection_success(self, mock_collection):
        """Vérifie la récupération de la collection."""
        import common.db as database
        from entreprise.functions import get_collection
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = get_collection("entreprise")
            
            mock_db.__getitem__.assert_called_with("users_entreprise")

    def test_get_collection_db_not_initialized(self):
        """Vérifie le rejet si DB non initialisée."""
        import common.db as database
        from entreprise.functions import get_collection
        
        with patch.object(database, 'db', None):
            with pytest.raises(HTTPException) as exc_info:
                get_collection("entreprise")
            
            assert exc_info.value.status_code == 500
            assert "DB" in exc_info.value.detail


class TestSerialize:
    """Tests pour la fonction serialize."""

    def test_serialize_document(self, sample_entreprise_data):
        """Vérifie la sérialisation d'un document."""
        from entreprise.functions import serialize
        
        result = serialize(sample_entreprise_data)
        
        assert result["_id"] == str(sample_entreprise_data["_id"])
        assert result["raisonSociale"] == "Tech Solutions SA"
        assert result["siret"] == "12345678901234"
        assert result["email"] == "contact@techsolutions.fr"
        assert result["role"] == "entreprise"

    def test_serialize_none_returns_none(self):
        """Vérifie que None retourne None."""
        from entreprise.functions import serialize
        
        result = serialize(None)
        
        assert result is None


# =====================
# Tests de listage
# =====================

class TestListerEntreprises:
    """Tests pour le listage des entreprises."""

    @pytest.mark.asyncio
    async def test_lister_entreprises_success(
        self, sample_entreprise_data, mock_collection, async_cursor_factory
    ):
        """Vérifie le listage réussi."""
        import common.db as database
        from entreprise.functions import lister_entreprises
        
        cursor = async_cursor_factory([sample_entreprise_data])
        cursor.sort = MagicMock(return_value=cursor)
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await lister_entreprises()
            
            assert "entreprises" in result
            assert len(result["entreprises"]) == 1
            assert result["entreprises"][0]["raisonSociale"] == "Tech Solutions SA"

    @pytest.mark.asyncio
    async def test_lister_entreprises_empty(self, mock_collection, async_cursor_factory):
        """Vérifie le listage vide."""
        import common.db as database
        from entreprise.functions import lister_entreprises
        
        cursor = async_cursor_factory([])
        cursor.sort = MagicMock(return_value=cursor)
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await lister_entreprises()
            
            assert result["entreprises"] == []


class TestListerEntreprisesRoute:
    """Tests d'intégration pour la route de listage."""

    def test_list_entreprises_route(
        self, client, sample_entreprise_data, mock_collection, async_cursor_factory
    ):
        """Vérifie la route de listage."""
        import common.db as database
        
        cursor = async_cursor_factory([sample_entreprise_data])
        cursor.sort = MagicMock(return_value=cursor)
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get("/entreprise/")
            
            assert response.status_code == 200
            data = response.json()
            assert "entreprises" in data


# =====================
# Tests de récupération des infos complètes
# =====================

class TestRecupererInfosEntrepriseCompletes:
    """Tests pour la récupération des infos complètes."""

    @pytest.mark.asyncio
    async def test_recuperer_infos_success(self, sample_entreprise_data, mock_collection):
        """Vérifie la récupération réussie."""
        import common.db as database
        from entreprise.functions import recuperer_infos_entreprise_completes
        
        mock_collection.find_one = AsyncMock(return_value=sample_entreprise_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await recuperer_infos_entreprise_completes(
                str(sample_entreprise_data["_id"])
            )
            
            assert result["message"] == "Données récupérées avec succès"
            assert result["data"]["raisonSociale"] == "Tech Solutions SA"

    @pytest.mark.asyncio
    async def test_recuperer_infos_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvée."""
        import common.db as database
        from entreprise.functions import recuperer_infos_entreprise_completes
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await recuperer_infos_entreprise_completes(str(ObjectId()))
            
            assert exc_info.value.status_code == 404


class TestRecupererInfosEntrepriseCompletesRoute:
    """Tests d'intégration pour la route infos complètes."""

    def test_get_infos_completes_route(
        self, client, sample_entreprise_data, mock_collection
    ):
        """Vérifie la route infos complètes."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_entreprise_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(
                f"/entreprise/infos-completes/{sample_entreprise_data['_id']}"
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
            
            response = client.get(f"/entreprise/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de création
# =====================

class TestCreerEntreprise:
    """Tests pour la création d'entreprise."""

    @pytest.mark.asyncio
    async def test_creer_entreprise_success(self, sample_entreprise_data, mock_collection):
        """Vérifie la création réussie."""
        import common.db as database
        from entreprise.functions import creer_entreprise
        from entreprise.models import Entity
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_entreprise_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_entreprise_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = Entity(
                raisonSociale="Tech Solutions SA",
                siret="12345678901234",
                adresse="10 Avenue des Champs, 75008 Paris",
                email="contact@techsolutions.fr"
            )
            
            result = await creer_entreprise(payload)
            
            assert result["message"] == "Entreprise créée"
            assert result["data"]["raisonSociale"] == "Tech Solutions SA"


class TestCreerEntrepriseRoute:
    """Tests d'intégration pour la route de création."""

    def test_create_entreprise_route(self, client, sample_entreprise_data, mock_collection):
        """Vérifie la route de création."""
        import common.db as database
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_entreprise_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_entreprise_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/entreprise/", json={
                "raisonSociale": "Tech Solutions SA",
                "siret": "12345678901234",
                "adresse": "10 Avenue des Champs, 75008 Paris",
                "email": "contact@techsolutions.fr"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Entreprise créée"


# =====================
# Tests de mise à jour
# =====================

class TestMettreAJourEntreprise:
    """Tests pour la mise à jour d'entreprise."""

    @pytest.mark.asyncio
    async def test_update_entreprise_success(self, sample_entreprise_data, mock_collection):
        """Vérifie la mise à jour réussie."""
        import common.db as database
        from entreprise.functions import mettre_a_jour_entreprise
        from entreprise.models import EntityUpdate
        
        updated_data = sample_entreprise_data.copy()
        updated_data["adresse"] = "12 Avenue des Champs, 75008 Paris"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = EntityUpdate(adresse="12 Avenue des Champs, 75008 Paris")
            result = await mettre_a_jour_entreprise(
                str(sample_entreprise_data["_id"]),
                payload
            )
            
            assert result["message"] == "Entreprise mise à jour"

    @pytest.mark.asyncio
    async def test_update_entreprise_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvée."""
        import common.db as database
        from entreprise.functions import mettre_a_jour_entreprise
        from entreprise.models import EntityUpdate
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = EntityUpdate(adresse="12 Avenue des Champs, 75008 Paris")
            
            with pytest.raises(HTTPException) as exc_info:
                await mettre_a_jour_entreprise(str(ObjectId()), payload)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_entreprise_empty_payload(self, mock_collection):
        """Vérifie le rejet si payload vide."""
        import common.db as database
        from entreprise.functions import mettre_a_jour_entreprise
        from entreprise.models import EntityUpdate
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = EntityUpdate()
            
            with pytest.raises(HTTPException) as exc_info:
                await mettre_a_jour_entreprise(str(ObjectId()), payload)
            
            assert exc_info.value.status_code == 400


class TestMettreAJourEntrepriseRoute:
    """Tests d'intégration pour la route de mise à jour."""

    def test_update_entreprise_route(self, client, sample_entreprise_data, mock_collection):
        """Vérifie la route de mise à jour."""
        import common.db as database
        
        updated_data = sample_entreprise_data.copy()
        updated_data["adresse"] = "12 Avenue des Champs, 75008 Paris"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/entreprise/{sample_entreprise_data['_id']}",
                json={"adresse": "12 Avenue des Champs, 75008 Paris"}
            )
            
            assert response.status_code == 200


# =====================
# Tests de suppression
# =====================

class TestSupprimerEntreprise:
    """Tests pour la suppression d'entreprise."""

    @pytest.mark.asyncio
    async def test_supprimer_entreprise_success(self, sample_entreprise_data, mock_collection):
        """Vérifie la suppression réussie."""
        import common.db as database
        from entreprise.functions import supprimer_entreprise
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await supprimer_entreprise(str(sample_entreprise_data["_id"]))
            
            assert result["message"] == "Entreprise supprimée"
            assert result["entreprise_id"] == str(sample_entreprise_data["_id"])

    @pytest.mark.asyncio
    async def test_supprimer_entreprise_not_found(self, mock_collection):
        """Vérifie le rejet si non trouvée."""
        import common.db as database
        from entreprise.functions import supprimer_entreprise
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await supprimer_entreprise(str(ObjectId()))
            
            assert exc_info.value.status_code == 404


class TestSupprimerEntrepriseRoute:
    """Tests d'intégration pour la route de suppression."""

    def test_delete_entreprise_route(self, client, sample_entreprise_data, mock_collection):
        """Vérifie la route de suppression."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/entreprise/{sample_entreprise_data['_id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Entreprise supprimée"

    def test_delete_entreprise_not_found_route(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/entreprise/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de validation
# =====================

class TestEntreprisePayloadValidation:
    """Tests de validation des payloads entreprise."""

    def test_create_missing_raison_sociale(self, client):
        """Vérifie le rejet sans raison sociale."""
        response = client.post("/entreprise/", json={
            "siret": "12345678901234",
            "email": "contact@techsolutions.fr"
        })
        
        assert response.status_code == 422

    def test_create_invalid_email(self, client):
        """Vérifie le rejet pour email invalide."""
        response = client.post("/entreprise/", json={
            "raisonSociale": "Tech Solutions SA",
            "siret": "12345678901234",
            "email": "invalid-email"
        })
        
        assert response.status_code == 422
