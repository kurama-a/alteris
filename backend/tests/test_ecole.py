"""
Tests pour le module Ecole.
Tests de gestion des écoles partenaires.
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
    """Crée une instance de l'application Ecole."""
    from fastapi import FastAPI
    from ecole.routes import ecole_api
    
    app = FastAPI()
    app.include_router(ecole_api, prefix="/ecole")
    return app


@pytest.fixture
def client(app):
    """Client pour l'API Ecole."""
    return TestClient(app)


# =====================
# Fixtures spécifiques
# =====================

@pytest.fixture
def sample_ecole_data():
    """Données d'une école de test."""
    return {
        "_id": ObjectId(),
        "raisonSociale": "ESGI Paris",
        "siret": "98765432109876",
        "adresse": "242 Rue du Faubourg Saint-Antoine, 75012 Paris",
        "email": "contact@esgi.fr",
        "creeLe": datetime.utcnow().isoformat(),
        "role": "ecole"
    }


# =====================
# Tests des routes Health
# =====================

class TestEcoleHealth:
    """Tests pour la route health de l'école."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/ecole/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ecole"


# =====================
# Tests des modèles
# =====================

class TestEcoleModels:
    """Tests pour les modèles Ecole."""

    def test_health_response_model(self):
        """Vérifie le modèle HealthResponse."""
        from ecole.models import HealthResponse
        
        response = HealthResponse(status="ok", service="ecole")
        
        assert response.status == "ok"
        assert response.service == "ecole"

    def test_entity_model(self):
        """Vérifie le modèle Entity."""
        from ecole.models import Entity
        
        entity = Entity(
            raisonSociale="ESGI Paris",
            siret="98765432109876",
            adresse="242 Rue du Faubourg Saint-Antoine, 75012 Paris",
            email="contact@esgi.fr"
        )
        
        assert entity.raisonSociale == "ESGI Paris"
        assert entity.siret == "98765432109876"

    def test_entity_update_model(self):
        """Vérifie le modèle EntityUpdate."""
        from ecole.models import EntityUpdate
        
        update = EntityUpdate(
            raisonSociale="ESGI Paris Campus Innovation",
            adresse="250 Rue du Faubourg Saint-Antoine, 75012 Paris"
        )
        
        assert update.raisonSociale == "ESGI Paris Campus Innovation"


# =====================
# Tests de récupération des infos complètes
# =====================

class TestRecupererInfosEcoleCompletes:
    """Tests pour la récupération des infos complètes."""

    def test_get_infos_completes_route(self, client, sample_ecole_data, mock_collection):
        """Vérifie la route infos complètes."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_ecole_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/ecole/infos-completes/{sample_ecole_data['_id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Données récupérées avec succès"

    def test_get_infos_completes_not_found(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/ecole/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de création
# =====================

class TestCreerEcole:
    """Tests pour la création d'école."""

    def test_create_ecole_route(self, client, sample_ecole_data, mock_collection):
        """Vérifie la route de création."""
        import common.db as database
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_ecole_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_ecole_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/ecole/", json={
                "raisonSociale": "ESGI Paris",
                "siret": "98765432109876",
                "adresse": "242 Rue du Faubourg Saint-Antoine, 75012 Paris",
                "email": "contact@esgi.fr"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "École créée"


# =====================
# Tests de mise à jour
# =====================

class TestMettreAJourEcole:
    """Tests pour la mise à jour d'école."""

    def test_update_ecole_route(self, client, sample_ecole_data, mock_collection):
        """Vérifie la route de mise à jour."""
        import common.db as database
        
        updated_data = sample_ecole_data.copy()
        updated_data["adresse"] = "250 Rue du Faubourg Saint-Antoine, 75012 Paris"
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/ecole/{sample_ecole_data['_id']}",
                json={"adresse": "250 Rue du Faubourg Saint-Antoine, 75012 Paris"}
            )
            
            assert response.status_code == 200

    def test_update_ecole_not_found(self, client, mock_collection):
        """Vérifie le rejet 404 si non trouvée."""
        import common.db as database
        
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.put(
                f"/ecole/{ObjectId()}",
                json={"adresse": "250 Rue du Faubourg Saint-Antoine, 75012 Paris"}
            )
            
            assert response.status_code == 404


# =====================
# Tests de suppression
# =====================

class TestSupprimerEcole:
    """Tests pour la suppression d'école."""

    def test_delete_ecole_route(self, client, sample_ecole_data, mock_collection):
        """Vérifie la route de suppression."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/ecole/{sample_ecole_data['_id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "École supprimée"

    def test_delete_ecole_not_found_route(self, client, mock_collection):
        """Vérifie le rejet 404 sur la route."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/ecole/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests de validation
# =====================

class TestEcolePayloadValidation:
    """Tests de validation des payloads école."""

    def test_create_missing_raison_sociale(self, client):
        """Vérifie le rejet sans raison sociale."""
        response = client.post("/ecole/", json={
            "siret": "98765432109876",
            "email": "contact@esgi.fr"
        })
        
        assert response.status_code == 422

    def test_create_invalid_email(self, client):
        """Vérifie le rejet pour email invalide."""
        response = client.post("/ecole/", json={
            "raisonSociale": "ESGI Paris",
            "siret": "98765432109876",
            "email": "invalid-email"
        })
        
        assert response.status_code == 422


# =====================
# Tests fonctions
# =====================

class TestEcoleFunctions:
    """Tests pour les fonctions du module école."""

    @pytest.mark.asyncio
    async def test_creer_ecole(self, sample_ecole_data, mock_collection):
        """Vérifie la fonction creer_ecole."""
        import common.db as database
        from ecole.functions import creer_ecole
        from ecole.models import Entity
        
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=sample_ecole_data["_id"])
        )
        mock_collection.find_one = AsyncMock(return_value=sample_ecole_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = Entity(
                raisonSociale="ESGI Paris",
                siret="98765432109876",
                adresse="242 Rue du Faubourg Saint-Antoine, 75012 Paris",
                email="contact@esgi.fr"
            )
            
            result = await creer_ecole(payload)
            
            assert result["message"] == "École créée"

    @pytest.mark.asyncio
    async def test_supprimer_ecole(self, sample_ecole_data, mock_collection):
        """Vérifie la fonction supprimer_ecole."""
        import common.db as database
        from ecole.functions import supprimer_ecole
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await supprimer_ecole(str(sample_ecole_data["_id"]))
            
            assert result["message"] == "École supprimée"
            assert result["ecole_id"] == str(sample_ecole_data["_id"])
