"""
Tests pour le module Jury.
Tests de gestion des jurys de soutenance.
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
    """Crée une instance de l'application Jury."""
    from fastapi import FastAPI
    from jury.routes import jury_api
    
    app = FastAPI()
    app.include_router(jury_api, prefix="/jury")
    return app


@pytest.fixture
def client(app):
    """Client pour l'API Jury."""
    return TestClient(app)


# =====================
# Fixtures spécifiques aux jurys
# =====================

@pytest.fixture
def sample_jury_data(sample_object_ids, sample_tuteur_data, sample_professeur_data, sample_apprenti_data):
    """Données d'un jury de test."""
    return {
        "_id": ObjectId(),
        "promotion_reference": {
            "promotion_id": sample_object_ids["promotion"],
            "annee_academique": "E5a",
            "label": "Promotion E5a 2024-2025",
            "semester_id": str(ObjectId()),
            "semester_name": "S9"
        },
        "semestre_reference": "S9",
        "date": datetime.utcnow().isoformat(),
        "status": "planifie",
        "members": {
            "tuteur": {
                "user_id": str(sample_tuteur_data["_id"]),
                "role": "tuteur_pedagogique",
                "first_name": sample_tuteur_data["first_name"],
                "last_name": sample_tuteur_data["last_name"],
                "email": sample_tuteur_data["email"]
            },
            "professeur": {
                "user_id": str(sample_professeur_data["_id"]),
                "role": "professeur",
                "first_name": sample_professeur_data["first_name"],
                "last_name": sample_professeur_data["last_name"],
                "email": sample_professeur_data["email"]
            },
            "apprenti": {
                "user_id": str(sample_apprenti_data["_id"]),
                "role": "apprenti",
                "first_name": sample_apprenti_data["first_name"],
                "last_name": sample_apprenti_data["last_name"],
                "email": sample_apprenti_data["email"]
            },
            "intervenant": {
                "user_id": str(ObjectId()),
                "role": "intervenant",
                "first_name": "Expert",
                "last_name": "Externe",
                "email": "expert@example.com"
            }
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# =====================
# Tests des routes Health
# =====================

class TestJuryHealth:
    """Tests pour la route health du jury."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/jury/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "jury"


class TestJuryProfile:
    """Tests pour le profil jury."""

    def test_get_profile(self, client):
        """Vérifie la route profil."""
        response = client.get("/jury/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


# =====================
# Tests des modèles Jury
# =====================

class TestJuryModels:
    """Tests pour les modèles Jury."""

    def test_jury_status_enum(self):
        """Vérifie l'enum JuryStatus."""
        from jury.models import JuryStatus
        
        assert JuryStatus.planifie.value == "planifie"
        assert JuryStatus.termine.value == "termine"

    def test_member_details_model(self):
        """Vérifie le modèle MemberDetails."""
        from jury.models import MemberDetails
        
        member = MemberDetails(
            user_id=str(ObjectId()),
            role="tuteur_pedagogique",
            first_name="Marie",
            last_name="Martin",
            email="marie@example.com",
            phone="+33612345678"
        )
        
        assert member.first_name == "Marie"
        assert member.role == "tuteur_pedagogique"

    def test_jury_create_request_model(self, sample_object_ids):
        """Vérifie le modèle JuryCreateRequest."""
        from jury.models import JuryCreateRequest, JuryStatus
        
        request = JuryCreateRequest(
            promotion_id=sample_object_ids["promotion"],
            semester_id=str(ObjectId()),
            date=datetime.utcnow(),
            status=JuryStatus.planifie,
            tuteur_id=sample_object_ids["tuteur"],
            professeur_id=sample_object_ids["professeur"],
            apprenti_id=sample_object_ids["apprenti"],
            intervenant_id=str(ObjectId())
        )
        
        assert request.status == JuryStatus.planifie


# =====================
# Tests CRUD Jury
# =====================

class TestListJuries:
    """Tests pour la liste des jurys."""

    def test_list_juries_success(self, client, sample_jury_data, mock_collection, async_cursor_factory):
        """Vérifie la liste des jurys."""
        import common.db as database
        
        cursor = async_cursor_factory([sample_jury_data])
        cursor.sort = MagicMock(return_value=cursor)
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get("/jury/juries")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_list_juries_empty(self, client, mock_collection, async_cursor_factory):
        """Vérifie la liste vide."""
        import common.db as database
        
        cursor = async_cursor_factory([])
        cursor.sort = MagicMock(return_value=cursor)
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get("/jury/juries")
            
            assert response.status_code == 200
            assert response.json() == []


class TestGetJury:
    """Tests pour la récupération d'un jury."""

    def test_get_jury_success(self, client, sample_jury_data, mock_collection):
        """Vérifie la récupération d'un jury."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_jury_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/jury/juries/{sample_jury_data['_id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert "members" in data
            assert data["semestre_reference"] == "S9"

    def test_get_jury_not_found(self, client, mock_collection):
        """Vérifie le rejet si jury non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/jury/juries/{ObjectId()}")
            
            assert response.status_code == 404


class TestCreateJury:
    """Tests pour la création de jury."""

    def test_create_jury_success(
        self, client, sample_object_ids, sample_tuteur_data, sample_professeur_data,
        sample_apprenti_data, sample_promotion_data, mock_collection
    ):
        """Vérifie la création d'un jury."""
        import common.db as database
        
        # Mock pour les différentes collections
        tuteur_mock = AsyncMock()
        tuteur_mock.find_one = AsyncMock(return_value=sample_tuteur_data)
        
        professeur_mock = AsyncMock()
        professeur_mock.find_one = AsyncMock(return_value=sample_professeur_data)
        
        apprenti_mock = AsyncMock()
        apprenti_mock.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        intervenant_mock = AsyncMock()
        intervenant_mock.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "first_name": "Expert",
            "last_name": "Externe",
            "email": "expert@example.com"
        })
        
        promo_mock = AsyncMock()
        promo_mock.find_one = AsyncMock(return_value=sample_promotion_data)
        
        jury_mock = AsyncMock()
        jury_mock.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
        
        def get_collection(name):
            if "tuteur" in name:
                return tuteur_mock
            elif "professeur" in name:
                return professeur_mock
            elif "apprenti" in name:
                return apprenti_mock
            elif "intervenant" in name:
                return intervenant_mock
            elif "promos" in name:
                return promo_mock
            elif "juries" in name:
                return jury_mock
            return AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(side_effect=get_collection)
            
            response = client.post("/jury/juries", json={
                "promotion_id": sample_object_ids["promotion"],
                "semester_id": sample_promotion_data["semesters"][0]["semester_id"],
                "date": datetime.utcnow().isoformat(),
                "status": "planifie",
                "tuteur_id": sample_object_ids["tuteur"],
                "professeur_id": sample_object_ids["professeur"],
                "apprenti_id": sample_object_ids["apprenti"],
                "intervenant_id": str(ObjectId())
            })
            
            assert response.status_code == 200


class TestUpdateJury:
    """Tests pour la mise à jour de jury."""

    def test_update_jury_status(self, client, sample_jury_data, mock_collection):
        """Vérifie la mise à jour du statut."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_jury_data)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.patch(
                f"/jury/juries/{sample_jury_data['_id']}",
                json={"status": "termine"}
            )
            
            assert response.status_code == 200

    def test_update_jury_not_found(self, client, mock_collection):
        """Vérifie le rejet si jury non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.patch(
                f"/jury/juries/{ObjectId()}",
                json={"status": "termine"}
            )
            
            assert response.status_code == 404


class TestDeleteJury:
    """Tests pour la suppression de jury."""

    def test_delete_jury_success(self, client, mock_collection):
        """Vérifie la suppression réussie."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/jury/juries/{ObjectId()}")
            
            assert response.status_code == 200
            assert response.json()["status"] == "deleted"

    def test_delete_jury_not_found(self, client, mock_collection):
        """Vérifie le rejet si jury non trouvé."""
        import common.db as database
        
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(f"/jury/juries/{ObjectId()}")
            
            assert response.status_code == 404


# =====================
# Tests des promotions timeline
# =====================

class TestPromotionsTimeline:
    """Tests pour la liste des promotions et semestres."""

    def test_list_promotions_timeline(
        self, client, sample_promotion_data, mock_collection, async_cursor_factory
    ):
        """Vérifie la liste des promotions/semestres."""
        import common.db as database
        
        cursor = async_cursor_factory([sample_promotion_data])
        cursor.sort = MagicMock(return_value=cursor)
        mock_collection.find = MagicMock(return_value=cursor)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get("/jury/promotions-timeline")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# =====================
# Tests des fonctions utilitaires
# =====================

class TestJuryHelperFunctions:
    """Tests pour les fonctions utilitaires du module jury."""

    def test_parse_object_id_valid(self):
        """Vérifie le parsing d'un ID valide."""
        from jury.routes import _parse_object_id
        
        valid_id = str(ObjectId())
        result = _parse_object_id(valid_id)
        
        assert isinstance(result, ObjectId)

    def test_parse_object_id_invalid(self):
        """Vérifie le rejet d'un ID invalide."""
        from jury.routes import _parse_object_id
        
        with pytest.raises(HTTPException) as exc_info:
            _parse_object_id("invalid-id")
        
        assert exc_info.value.status_code == 400

    def test_serialize_jury(self, sample_jury_data):
        """Vérifie la sérialisation d'un jury."""
        from jury.routes import _serialize_jury
        
        result = _serialize_jury(sample_jury_data)
        
        # _serialize_jury retourne un JuryResponse (objet Pydantic), pas un dict
        assert hasattr(result, 'id')
        assert hasattr(result, 'members')
        assert hasattr(result, 'status')


# =====================
# Tests de validation
# =====================

class TestJuryPayloadValidation:
    """Tests de validation des payloads jury."""

    def test_create_jury_missing_promotion(self, client):
        """Vérifie le rejet sans promotion_id."""
        response = client.post("/jury/juries", json={
            "semester_id": str(ObjectId()),
            "date": datetime.utcnow().isoformat(),
            "status": "planifie",
            "tuteur_id": str(ObjectId()),
            "professeur_id": str(ObjectId()),
            "apprenti_id": str(ObjectId()),
            "intervenant_id": str(ObjectId())
        })
        
        assert response.status_code == 422

    def test_create_jury_invalid_status(self, client, sample_object_ids):
        """Vérifie le rejet pour un statut invalide."""
        response = client.post("/jury/juries", json={
            "promotion_id": sample_object_ids["promotion"],
            "semester_id": str(ObjectId()),
            "date": datetime.utcnow().isoformat(),
            "status": "invalid_status",
            "tuteur_id": sample_object_ids["tuteur"],
            "professeur_id": sample_object_ids["professeur"],
            "apprenti_id": sample_object_ids["apprenti"],
            "intervenant_id": str(ObjectId())
        })
        
        assert response.status_code == 422