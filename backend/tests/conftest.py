"""
Configuration et fixtures partagées pour tous les tests.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import sys
import os

# Ajouter le backend au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =====================
# Fixtures de base
# =====================

@pytest.fixture(scope="session")
def event_loop():
    """Crée un event loop pour les tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_object_id():
    """Génère un ObjectId valide pour les tests."""
    return str(ObjectId())


@pytest.fixture
def sample_object_ids():
    """Génère plusieurs ObjectIds pour les tests."""
    return {
        "apprenti": str(ObjectId()),
        "tuteur": str(ObjectId()),
        "maitre": str(ObjectId()),
        "entreprise": str(ObjectId()),
        "jury": str(ObjectId()),
        "professeur": str(ObjectId()),
        "coordinatrice": str(ObjectId()),
        "responsable_cursus": str(ObjectId()),
        "promotion": str(ObjectId()),
    }


# =====================
# Mock Database
# =====================

@pytest.fixture
def mock_db():
    """Mock de la base de données MongoDB."""
    mock = MagicMock()
    mock.__getitem__ = MagicMock(return_value=AsyncMock())
    return mock


@pytest.fixture
def mock_collection():
    """Mock d'une collection MongoDB."""
    collection = AsyncMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.find = MagicMock(return_value=AsyncMock())
    collection.insert_one = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    return collection


# =====================
# Données de test utilisateurs
# =====================

@pytest.fixture
def sample_apprenti_data(sample_object_ids):
    """Données d'un apprenti de test."""
    return {
        "_id": ObjectId(sample_object_ids["apprenti"]),
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@reseaualternance.fr",
        "phone": "+33612345678",
        "age": 22,
        "annee_academique": "E5a",
        "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X0.R1LT8OY.6B0bSO",  # hashed "password123"
        "role": "apprenti",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "tuteur": None,
        "maitre": None,
        "entretiens": [],
    }


@pytest.fixture
def sample_tuteur_data(sample_object_ids):
    """Données d'un tuteur pédagogique de test."""
    return {
        "_id": ObjectId(sample_object_ids["tuteur"]),
        "first_name": "Marie",
        "last_name": "Martin",
        "email": "marie.martin@tuteurs.reseaualternance.fr",
        "phone": "+33698765432",
        "role": "tuteur_pedagogique",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_maitre_data(sample_object_ids):
    """Données d'un maître d'apprentissage de test."""
    return {
        "_id": ObjectId(sample_object_ids["maitre"]),
        "first_name": "Pierre",
        "last_name": "Bernard",
        "email": "pierre.bernard@maitre.reseaualternance.fr",
        "phone": "+33654321098",
        "role": "maitre_apprentissage",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_entreprise_data(sample_object_ids):
    """Données d'une entreprise de test."""
    return {
        "_id": ObjectId(sample_object_ids["entreprise"]),
        "raisonSociale": "TechCorp SAS",
        "siret": "12345678900011",
        "adresse": "123 Rue de la Tech, 75001 Paris",
        "email": "contact@techcorp.fr",
        "role": "entreprise",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_professeur_data(sample_object_ids):
    """Données d'un professeur de test."""
    return {
        "_id": ObjectId(sample_object_ids["professeur"]),
        "first_name": "Sophie",
        "last_name": "Leroy",
        "email": "sophie.leroy@eseo.fr",
        "phone": "+33611223344",
        "role": "professeur",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_coordinatrice_data(sample_object_ids):
    """Données d'une coordinatrice de test."""
    return {
        "_id": ObjectId(sample_object_ids["coordinatrice"]),
        "first_name": "Isabelle",
        "last_name": "Moreau",
        "email": "isabelle.moreau@coordination.reseaualternance.fr",
        "phone": "+33699887766",
        "role": "coordinatrice",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_responsable_cursus_data(sample_object_ids):
    """Données d'un responsable de cursus de test."""
    return {
        "_id": ObjectId(sample_object_ids["responsable_cursus"]),
        "first_name": "François",
        "last_name": "Petit",
        "email": "francois.petit@cursus.reseaualternance.fr",
        "phone": "+33677889900",
        "role": "responsable_cursus",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_promotion_data(sample_object_ids, sample_apprenti_data):
    """Données d'une promotion de test."""
    return {
        "_id": ObjectId(sample_object_ids["promotion"]),
        "annee_academique": "E5a",
        "label": "Promotion E5a 2024-2025",
        "apprentis": [
            {
                "_id": str(sample_apprenti_data["_id"]),
                "first_name": sample_apprenti_data["first_name"],
                "last_name": sample_apprenti_data["last_name"],
                "email": sample_apprenti_data["email"],
            }
        ],
        "nb_apprentis": 1,
        "coordinators": [],
        "next_milestone": "Soutenance S9",
        "semesters": [
            {
                "semester_id": str(ObjectId()),
                "name": "S9",
                "start_date": "2024-09-01",
                "end_date": "2025-01-31",
                "order": 0,
                "deliverables": [
                    {
                        "deliverable_id": str(ObjectId()),
                        "title": "Rapport de stage",
                        "due_date": "2025-01-15",
                        "order": 0,
                    }
                ],
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_entretien_data(sample_object_ids):
    """Données d'un entretien de test."""
    return {
        "entretien_id": str(ObjectId()),
        "apprenti_id": sample_object_ids["apprenti"],
        "apprenti_nom": "Jean Dupont",
        "date": datetime.utcnow().isoformat(),
        "sujet": "Suivi semestriel S9",
        "created_at": datetime.utcnow().isoformat(),
        "tuteur": {
            "tuteur_id": sample_object_ids["tuteur"],
            "first_name": "Marie",
            "last_name": "Martin",
            "email": "marie.martin@tuteurs.reseaualternance.fr",
        },
        "maitre": {
            "maitre_id": sample_object_ids["maitre"],
            "first_name": "Pierre",
            "last_name": "Bernard",
            "email": "pierre.bernard@maitre.reseaualternance.fr",
        },
        "note": None,
    }


@pytest.fixture
def sample_document_data():
    """Données d'un document de test."""
    return {
        "id": str(ObjectId()),
        "semester_id": str(ObjectId()),
        "category": "rapport",
        "file_name": "rapport_stage.pdf",
        "file_size": 1024000,
        "file_type": "application/pdf",
        "uploaded_at": datetime.utcnow(),
        "uploader_id": str(ObjectId()),
        "uploader_name": "Jean Dupont",
        "uploader_role": "apprenti",
        "download_url": "/documents/test/download",
        "comments": [],
    }


# =====================
# JWT Token fixtures
# =====================

@pytest.fixture
def sample_token_payload(sample_object_ids):
    """Payload JWT de test."""
    return {
        "sub": "jean.dupont@reseaualternance.fr",
        "role": "apprenti",
        "user_id": sample_object_ids["apprenti"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }


@pytest.fixture
def valid_token():
    """Token JWT valide pour les tests."""
    from jose import jwt
    payload = {
        "sub": "jean.dupont@reseaualternance.fr",
        "role": "apprenti",
        "user_id": str(ObjectId()),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, "ton_secret_key_super_secure", algorithm="HS256")


@pytest.fixture
def expired_token():
    """Token JWT expiré pour les tests."""
    from jose import jwt
    payload = {
        "sub": "jean.dupont@reseaualternance.fr",
        "role": "apprenti",
        "user_id": str(ObjectId()),
        "exp": datetime.utcnow() - timedelta(hours=1),
    }
    return jwt.encode(payload, "ton_secret_key_super_secure", algorithm="HS256")


# =====================
# Request payloads
# =====================

@pytest.fixture
def register_user_payload():
    """Payload pour l'enregistrement d'un utilisateur."""
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
        "phone": "+33600000000",
        "age": 25,
        "annee_academique": "E5a",
        "password": "SecurePassword123!",
        "role": "apprenti",
    }


@pytest.fixture
def login_payload():
    """Payload pour la connexion."""
    return {
        "email": "jean.dupont@reseaualternance.fr",
        "password": "password123",
    }


@pytest.fixture
def update_me_payload():
    """Payload pour la mise à jour du profil."""
    return {
        "email": "nouveau.email@example.com",
        "current_password": "password123",
        "new_password": "NewSecurePassword456!",
        "confirm_password": "NewSecurePassword456!",
    }


# =====================
# Helpers
# =====================

def create_async_mock_cursor(data: list):
    """Crée un mock de curseur MongoDB async."""
    async def async_generator():
        for item in data:
            yield item
    
    cursor = MagicMock()
    cursor.__aiter__ = lambda self: async_generator()
    cursor.to_list = AsyncMock(return_value=data)
    return cursor


@pytest.fixture
def async_cursor_factory():
    """Factory pour créer des curseurs async mock."""
    return create_async_mock_cursor
