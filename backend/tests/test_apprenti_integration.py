"""
Tests d'intégration pour le module Apprenti.
Tests des routes API des apprentis.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

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
    from apprenti.routes import apprenti_api
    
    app = FastAPI()
    app.include_router(apprenti_api, prefix="/apprenti")
    return app


@pytest.fixture
def client(app):
    """Crée un client de test synchrone."""
    return TestClient(app)


# =====================
# Tests des routes Health
# =====================

class TestHealthRoute:
    """Tests pour la route GET /apprenti/health."""

    def test_health_returns_ok(self, client):
        """Vérifie que la route health retourne OK."""
        response = client.get("/apprenti/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "apprenti"


# =====================
# Tests des routes Infos
# =====================

class TestInfosCompletesRoute:
    """Tests pour la route GET /apprenti/infos-completes/{apprenti_id}."""

    def test_get_infos_success(self, client, sample_apprenti_data, mock_collection):
        """Vérifie la récupération des infos complètes."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/apprenti/infos-completes/{sample_apprenti_data['_id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert data["data"]["email"] == "jean.dupont@reseaualternance.fr"

    def test_get_infos_not_found(self, client, mock_collection):
        """Vérifie le rejet si apprenti non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/apprenti/infos-completes/{ObjectId()}")
            
            assert response.status_code == 404

    def test_get_infos_invalid_id(self, client):
        """Vérifie le rejet pour un ID invalide."""
        response = client.get("/apprenti/infos-completes/invalid-id")
        
        assert response.status_code == 500  # ObjectId invalide


# =====================
# Tests des routes Entretien
# =====================

class TestEntretienRoutes:
    """Tests pour les routes de gestion des entretiens."""

    def test_create_entretien_success(
        self, client, sample_apprenti_data, sample_tuteur_data, sample_maitre_data, mock_collection
    ):
        """Vérifie la création d'un entretien."""
        import common.db as database
        
        sample_apprenti_data["tuteur"] = {
            "tuteur_id": str(sample_tuteur_data["_id"]),
            "first_name": "Marie",
            "last_name": "Martin",
            "email": "marie@example.com"
        }
        sample_apprenti_data["maitre"] = {
            "maitre_id": str(sample_maitre_data["_id"]),
            "first_name": "Pierre",
            "last_name": "Bernard",
            "email": "pierre@example.com"
        }
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/apprenti/entretien/create", json={
                "apprenti_id": str(sample_apprenti_data["_id"]),
                "date": datetime.utcnow().isoformat(),
                "sujet": "Suivi semestriel"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "entretien" in data

    def test_create_entretien_missing_tuteur(self, client, sample_apprenti_data, mock_collection):
        """Vérifie le rejet si tuteur manquant."""
        import common.db as database
        
        sample_apprenti_data["tuteur"] = None
        sample_apprenti_data["maitre"] = None
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/apprenti/entretien/create", json={
                "apprenti_id": str(sample_apprenti_data["_id"]),
                "date": datetime.utcnow().isoformat(),
                "sujet": "Suivi semestriel"
            })
            
            assert response.status_code == 400

    def test_delete_entretien_success(self, client, sample_apprenti_data, mock_collection):
        """Vérifie la suppression d'un entretien."""
        import common.db as database
        
        entretien_id = str(ObjectId())
        sample_apprenti_data["entretiens"] = [{"entretien_id": entretien_id}]
        sample_apprenti_data["tuteur"] = {"tuteur_id": str(ObjectId())}
        sample_apprenti_data["maitre"] = {"maitre_id": str(ObjectId())}
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(
                f"/apprenti/entretien/{sample_apprenti_data['_id']}/{entretien_id}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["entretien_id"] == entretien_id

    def test_noter_entretien_success(self, client, sample_apprenti_data, sample_object_ids, mock_collection):
        """Vérifie la notation d'un entretien."""
        import common.db as database
        
        tuteur_id = sample_object_ids["tuteur"]
        entretien_id = str(ObjectId())
        sample_apprenti_data["tuteur"] = {"tuteur_id": tuteur_id}
        sample_apprenti_data["maitre"] = {"maitre_id": str(ObjectId())}
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post(
                f"/apprenti/entretien/{sample_apprenti_data['_id']}/{entretien_id}/note",
                json={"tuteur_id": tuteur_id, "note": 15.0}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["note"] == 15.0


# =====================
# Tests des routes Documents
# =====================

class TestDocumentRoutes:
    """Tests pour les routes de gestion des documents."""

    def test_get_documents_success(
        self, client, sample_apprenti_data, sample_promotion_data, mock_collection
    ):
        """Vérifie la liste des documents."""
        import common.db as database
        
        apprenti_mock = AsyncMock()
        apprenti_mock.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        promo_mock = AsyncMock()
        promo_mock.find_one = AsyncMock(return_value=sample_promotion_data)
        
        doc_mock = AsyncMock()
        doc_mock.find = MagicMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
        
        def get_collection(name):
            if "apprenti" in name:
                return apprenti_mock
            elif "promos" in name:
                return promo_mock
            else:
                return doc_mock
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(side_effect=get_collection)
            
            response = client.get(f"/apprenti/apprentis/{sample_apprenti_data['_id']}/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert "promotion" in data
            assert "semesters" in data
            assert "categories" in data

    def test_get_documents_apprenti_not_found(self, client, mock_collection):
        """Vérifie le rejet si apprenti non trouvé."""
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.get(f"/apprenti/apprentis/{ObjectId()}/documents")
            
            assert response.status_code == 404


class TestDocumentUpload:
    """Tests pour l'upload de documents."""

    def test_upload_document_wrong_uploader(
        self, client, sample_apprenti_data, sample_promotion_data, mock_collection
    ):
        """Vérifie le rejet si l'uploader n'est pas l'apprenti."""
        import common.db as database
        
        apprenti_mock = AsyncMock()
        apprenti_mock.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        promo_mock = AsyncMock()
        promo_mock.find_one = AsyncMock(return_value=sample_promotion_data)
        
        def get_collection(name):
            if "apprenti" in name:
                return apprenti_mock
            elif "promos" in name:
                return promo_mock
            return AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(side_effect=get_collection)
            
            # Créer un fichier de test
            test_file = io.BytesIO(b"Test content")
            
            response = client.post(
                f"/apprenti/apprentis/{sample_apprenti_data['_id']}/documents",
                data={
                    "category": "rapport",
                    "semester_id": sample_promotion_data["semesters"][0]["semester_id"],
                    "uploader_id": str(ObjectId()),  # Mauvais uploader
                    "uploader_name": "Wrong Person",
                    "uploader_role": "apprenti"
                },
                files={"file": ("test.doc", test_file, "application/msword")}
            )
            
            assert response.status_code == 403


class TestDocumentComments:
    """Tests pour les commentaires sur documents."""

    def test_add_comment_success(self, client, sample_apprenti_data, mock_collection):
        """Vérifie l'ajout d'un commentaire."""
        import common.db as database
        from apprenti.functions import add_document_comment
        
        document_id = str(ObjectId())
        document = {
            "_id": ObjectId(document_id),
            "apprentice_id": str(sample_apprenti_data["_id"]),
            "comments": []
        }
        
        mock_collection.find_one = AsyncMock(return_value=document)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post(
                f"/apprenti/apprentis/{sample_apprenti_data['_id']}/documents/{document_id}/comments",
                json={
                    "author_id": str(ObjectId()),
                    "author_name": "Marie Martin",
                    "author_role": "tuteur_pedagogique",
                    "content": "Bon travail !"
                }
            )
            
            assert response.status_code == 200


# =====================
# Tests des routes Compétences
# =====================

class TestCompetencyRoutes:
    """Tests pour les routes de gestion des compétences."""

    def test_get_competencies_success(
        self, client, sample_apprenti_data, sample_promotion_data, mock_collection
    ):
        """Vérifie la liste des évaluations de compétences."""
        import common.db as database
        
        apprenti_mock = AsyncMock()
        apprenti_mock.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        promo_mock = AsyncMock()
        promo_mock.find_one = AsyncMock(return_value=sample_promotion_data)
        
        competency_mock = AsyncMock()
        competency_mock.find_one = AsyncMock(return_value=None)  # No competency record yet
        
        def get_collection(name):
            if "apprenti" in name:
                return apprenti_mock
            elif "promos" in name:
                return promo_mock
            else:
                return competency_mock
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(side_effect=get_collection)
            
            response = client.get(f"/apprenti/apprentis/{sample_apprenti_data['_id']}/competences")
            
            assert response.status_code == 200
            data = response.json()
            assert "promotion" in data
            assert "semesters" in data
            assert "competencies" in data
            assert "levels" in data


# =====================
# Tests de validation des payloads
# =====================

class TestPayloadValidation:
    """Tests de validation des données d'entrée."""

    def test_entretien_missing_date(self, client):
        """Vérifie le rejet pour date manquante."""
        response = client.post("/apprenti/entretien/create", json={
            "apprenti_id": str(ObjectId()),
            "sujet": "Suivi semestriel"
            # date manquante
        })
        
        assert response.status_code == 422

    def test_entretien_missing_sujet(self, client):
        """Vérifie le rejet pour sujet manquant."""
        response = client.post("/apprenti/entretien/create", json={
            "apprenti_id": str(ObjectId()),
            "date": datetime.utcnow().isoformat()
            # sujet manquant
        })
        
        assert response.status_code == 422

    def test_note_invalid_type(self, client, sample_apprenti_data, sample_object_ids, mock_collection):
        """Vérifie le rejet pour une note de type invalide."""
        import common.db as database
        
        tuteur_id = sample_object_ids["tuteur"]
        sample_apprenti_data["tuteur"] = {"tuteur_id": tuteur_id}
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post(
                f"/apprenti/entretien/{sample_apprenti_data['_id']}/{ObjectId()}/note",
                json={"tuteur_id": tuteur_id, "note": "invalid"}
            )
            
            # Pydantic rejette le type invalide
            assert response.status_code == 422


# =====================
# Tests d'intégration complets
# =====================

class TestEntretienWorkflow:
    """Tests du workflow complet d'entretien."""

    def test_full_entretien_workflow(
        self, client, sample_apprenti_data, sample_tuteur_data, sample_maitre_data, 
        sample_object_ids, mock_collection
    ):
        """Vérifie le workflow complet: création -> notation -> suppression."""
        import common.db as database
        
        tuteur_id = sample_object_ids["tuteur"]
        entretien_id = str(ObjectId())
        
        sample_apprenti_data["tuteur"] = {
            "tuteur_id": tuteur_id,
            "first_name": "Marie",
            "last_name": "Martin",
            "email": "marie@example.com"
        }
        sample_apprenti_data["maitre"] = {
            "maitre_id": str(ObjectId()),
            "first_name": "Pierre",
            "last_name": "Bernard",
            "email": "pierre@example.com"
        }
        
        # Étape 1: Création
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post("/apprenti/entretien/create", json={
                "apprenti_id": str(sample_apprenti_data["_id"]),
                "date": datetime.utcnow().isoformat(),
                "sujet": "Entretien test"
            })
            
            assert response.status_code == 200

        # Étape 2: Notation
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.post(
                f"/apprenti/entretien/{sample_apprenti_data['_id']}/{entretien_id}/note",
                json={"tuteur_id": tuteur_id, "note": 16.5}
            )
            
            assert response.status_code == 200

        # Étape 3: Suppression
        sample_apprenti_data["entretiens"] = [{"entretien_id": entretien_id}]
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            response = client.delete(
                f"/apprenti/entretien/{sample_apprenti_data['_id']}/{entretien_id}"
            )
            
            assert response.status_code == 200