"""
Tests unitaires pour le module Apprenti.
Tests des fonctions de gestion des apprentis, entretiens, documents et compétences.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from pathlib import Path
import tempfile
import shutil

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBuildFullName:
    """Tests pour la construction du nom complet."""

    def test_build_full_name_with_first_last(self):
        """Vérifie le nom complet avec prénom et nom."""
        from apprenti.functions import _build_full_name
        
        apprenti = {"first_name": "Jean", "last_name": "Dupont"}
        assert _build_full_name(apprenti) == "Jean Dupont"

    def test_build_full_name_first_only(self):
        """Vérifie le nom complet avec prénom seul."""
        from apprenti.functions import _build_full_name
        
        apprenti = {"first_name": "Jean", "last_name": ""}
        assert _build_full_name(apprenti) == "Jean"

    def test_build_full_name_fallback_full_name(self):
        """Vérifie le repli sur full_name."""
        from apprenti.functions import _build_full_name
        
        apprenti = {"full_name": "Jean Dupont"}
        assert _build_full_name(apprenti) == "Jean Dupont"

    def test_build_full_name_fallback_email(self):
        """Vérifie le repli sur email."""
        from apprenti.functions import _build_full_name
        
        apprenti = {"email": "jean@example.com"}
        assert _build_full_name(apprenti) == "jean@example.com"

    def test_build_full_name_default(self):
        """Vérifie le repli par défaut."""
        from apprenti.functions import _build_full_name
        
        apprenti = {}
        assert _build_full_name(apprenti) == "Apprenti"


class TestBuildProfile:
    """Tests pour la construction du profil."""

    def test_build_profile_complete(self):
        """Vérifie le profil complet."""
        from apprenti.functions import _build_profile
        
        apprenti = {
            "profile": {
                "age": 22,
                "position": "Developpeur",
                "phone": "+33612345678",
                "city": "Paris",
                "avatarUrl": "https://example.com/avatar.jpg"
            }
        }
        
        profile = _build_profile(apprenti, "Jean Dupont")
        
        assert profile["age"] == 22
        assert profile["position"] == "Developpeur"
        assert profile["phone"] == "+33612345678"
        assert profile["city"] == "Paris"
        assert profile["avatarUrl"] == "https://example.com/avatar.jpg"

    def test_build_profile_defaults(self):
        """Vérifie les valeurs par défaut du profil."""
        from apprenti.functions import _build_profile
        
        apprenti = {}
        profile = _build_profile(apprenti, "Jean Dupont")
        
        assert profile["age"] == 0
        assert profile["position"] == "Apprenti"
        assert profile["phone"] == ""
        assert profile["city"] == ""
        assert "dicebear" in profile["avatarUrl"]


class TestBuildCompany:
    """Tests pour la construction des infos entreprise."""

    def test_build_company_complete(self):
        """Vérifie les infos entreprise complètes."""
        from apprenti.functions import _build_company
        
        apprenti = {
            "company": {
                "name": "TechCorp",
                "dates": "Sept 2024 - Août 2025",
                "address": "123 Rue Tech, Paris"
            }
        }
        
        company = _build_company(apprenti)
        
        assert company["name"] == "TechCorp"
        assert company["dates"] == "Sept 2024 - Août 2025"
        assert company["address"] == "123 Rue Tech, Paris"

    def test_build_company_defaults(self):
        """Vérifie les valeurs par défaut entreprise."""
        from apprenti.functions import _build_company
        
        apprenti = {}
        company = _build_company(apprenti)
        
        assert company["name"] == "Entreprise partenaire"
        assert company["dates"] == "Periode non renseignee"
        assert company["address"] == "Adresse non renseignee"


class TestBuildSchool:
    """Tests pour la construction des infos école."""

    def test_build_school_complete(self):
        """Vérifie les infos école complètes."""
        from apprenti.functions import _build_school
        
        apprenti = {
            "school": {
                "name": "ESEO",
                "program": "Cycle ingénieur"
            }
        }
        
        school = _build_school(apprenti)
        
        assert school["name"] == "ESEO"
        assert school["program"] == "Cycle ingénieur"

    def test_build_school_defaults(self):
        """Vérifie les valeurs par défaut école."""
        from apprenti.functions import _build_school
        
        apprenti = {}
        school = _build_school(apprenti)
        
        assert school["name"] == "ESEO"
        assert school["program"] == "Programme non renseigne"


class TestBuildTutors:
    """Tests pour la construction des infos tuteurs."""

    def test_build_tutors_complete(self):
        """Vérifie les infos tuteurs complètes."""
        from apprenti.functions import _build_tutors
        
        apprenti = {
            "maitre": {
                "first_name": "Pierre",
                "last_name": "Bernard",
                "role": "Maitre",
                "email": "pierre@example.com",
                "phone": "+33612345678"
            },
            "tuteur_pedagogique": {
                "first_name": "Marie",
                "last_name": "Martin",
                "role": "Tuteur",
                "email": "marie@example.com"
            }
        }
        
        tutors = _build_tutors(apprenti)
        
        assert tutors is not None
        assert tutors["enterprisePrimary"]["name"] == "Pierre Bernard"
        assert tutors["pedagogic"]["name"] == "Marie Martin"

    def test_build_tutors_none_when_empty(self):
        """Vérifie le retour None sans tuteurs."""
        from apprenti.functions import _build_tutors
        
        apprenti = {}
        tutors = _build_tutors(apprenti)
        
        assert tutors is None


class TestBuildJournalPayload:
    """Tests pour la construction du payload journal."""

    def test_build_journal_payload_complete(self, sample_apprenti_data):
        """Vérifie le payload journal complet."""
        from apprenti.functions import _build_journal_payload
        
        payload = _build_journal_payload(sample_apprenti_data)
        
        assert "id" in payload
        assert payload["email"] == "jean.dupont@reseaualternance.fr"
        assert payload["fullName"] == "Jean Dupont"
        assert "profile" in payload
        assert "company" in payload
        assert "school" in payload
        assert "journalHeroImageUrl" in payload


class TestRecupererInfosApprentCompletes:
    """Tests pour la récupération des infos complètes de l'apprenti."""

    @pytest.mark.asyncio
    async def test_recuperer_infos_success(self, sample_apprenti_data, mock_collection):
        """Vérifie la récupération réussie des infos."""
        from apprenti.functions import recuperer_infos_apprenti_completes
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await recuperer_infos_apprenti_completes(str(sample_apprenti_data["_id"]))
            
            assert "message" in result
            assert "data" in result
            assert result["data"]["email"] == "jean.dupont@reseaualternance.fr"

    @pytest.mark.asyncio
    async def test_recuperer_infos_not_found(self, mock_collection):
        """Vérifie le rejet si apprenti non trouvé."""
        from apprenti.functions import recuperer_infos_apprenti_completes
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await recuperer_infos_apprenti_completes(str(ObjectId()))
            
            assert exc_info.value.status_code == 404


class TestCreerEntretien:
    """Tests pour la création d'entretien."""

    @pytest.mark.asyncio
    async def test_creer_entretien_success(
        self, sample_apprenti_data, sample_tuteur_data, sample_maitre_data, mock_collection
    ):
        """Vérifie la création d'entretien réussie."""
        from apprenti.functions import creer_entretien
        from apprenti.models import CreerEntretienRequest
        import common.db as database
        
        # Ajouter les tuteurs à l'apprenti
        sample_apprenti_data["tuteur"] = {
            "tuteur_id": str(sample_tuteur_data["_id"]),
            "first_name": sample_tuteur_data["first_name"],
            "last_name": sample_tuteur_data["last_name"],
            "email": sample_tuteur_data["email"]
        }
        sample_apprenti_data["maitre"] = {
            "maitre_id": str(sample_maitre_data["_id"]),
            "first_name": sample_maitre_data["first_name"],
            "last_name": sample_maitre_data["last_name"],
            "email": sample_maitre_data["email"]
        }
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            data = CreerEntretienRequest(
                apprenti_id=str(sample_apprenti_data["_id"]),
                date=datetime.utcnow(),
                sujet="Entretien semestriel"
            )
            
            result = await creer_entretien(data)
            
            assert "message" in result
            assert "entretien" in result
            assert result["entretien"]["sujet"] == "Entretien semestriel"

    @pytest.mark.asyncio
    async def test_creer_entretien_no_tuteur(self, sample_apprenti_data, mock_collection):
        """Vérifie le rejet sans tuteur associé."""
        from apprenti.functions import creer_entretien
        from apprenti.models import CreerEntretienRequest
        import common.db as database
        
        # Supprimer les tuteurs
        sample_apprenti_data["tuteur"] = None
        sample_apprenti_data["maitre"] = None
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            data = CreerEntretienRequest(
                apprenti_id=str(sample_apprenti_data["_id"]),
                date=datetime.utcnow(),
                sujet="Entretien semestriel"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await creer_entretien(data)
            
            assert exc_info.value.status_code == 400


class TestSupprimerEntretien:
    """Tests pour la suppression d'entretien."""

    @pytest.mark.asyncio
    async def test_supprimer_entretien_success(self, sample_apprenti_data, mock_collection):
        """Vérifie la suppression réussie."""
        from apprenti.functions import supprimer_entretien
        import common.db as database
        
        entretien_id = str(ObjectId())
        sample_apprenti_data["entretiens"] = [{"entretien_id": entretien_id}]
        sample_apprenti_data["tuteur"] = {"tuteur_id": str(ObjectId())}
        sample_apprenti_data["maitre"] = {"maitre_id": str(ObjectId())}
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await supprimer_entretien(str(sample_apprenti_data["_id"]), entretien_id)
            
            assert "message" in result
            assert result["entretien_id"] == entretien_id


class TestNoterEntretien:
    """Tests pour la notation d'entretien."""

    @pytest.mark.asyncio
    async def test_noter_entretien_success(self, sample_apprenti_data, sample_object_ids, mock_collection):
        """Vérifie la notation réussie."""
        from apprenti.functions import noter_entretien
        import common.db as database
        
        tuteur_id = sample_object_ids["tuteur"]
        entretien_id = str(ObjectId())
        sample_apprenti_data["tuteur"] = {"tuteur_id": tuteur_id}
        sample_apprenti_data["entretiens"] = [{"entretien_id": entretien_id, "note": None}]
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await noter_entretien(
                str(sample_apprenti_data["_id"]),
                entretien_id,
                tuteur_id=tuteur_id,
                note=15.5
            )
            
            assert result["note"] == 15.5
            assert result["entretien_id"] == entretien_id

    @pytest.mark.asyncio
    async def test_noter_entretien_wrong_tuteur(self, sample_apprenti_data, mock_collection):
        """Vérifie le rejet si ce n'est pas le bon tuteur."""
        from apprenti.functions import noter_entretien
        import common.db as database
        
        sample_apprenti_data["tuteur"] = {"tuteur_id": str(ObjectId())}
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await noter_entretien(
                    str(sample_apprenti_data["_id"]),
                    str(ObjectId()),
                    tuteur_id=str(ObjectId()),  # Mauvais tuteur
                    note=15.0
                )
            
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_noter_entretien_invalid_note(self, sample_apprenti_data, sample_object_ids, mock_collection):
        """Vérifie le rejet pour une note invalide."""
        from apprenti.functions import noter_entretien
        import common.db as database
        
        tuteur_id = sample_object_ids["tuteur"]
        sample_apprenti_data["tuteur"] = {"tuteur_id": tuteur_id}
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            with pytest.raises(HTTPException) as exc_info:
                await noter_entretien(
                    str(sample_apprenti_data["_id"]),
                    str(ObjectId()),
                    tuteur_id=tuteur_id,
                    note=25.0  # Note > 20
                )
            
            assert exc_info.value.status_code == 400


class TestDocumentDefinitions:
    """Tests pour les définitions de documents."""

    def test_document_definitions_exist(self):
        """Vérifie que les définitions existent."""
        from apprenti.functions import DOCUMENT_DEFINITIONS
        
        assert len(DOCUMENT_DEFINITIONS) > 0
        
        for definition in DOCUMENT_DEFINITIONS:
            assert "id" in definition
            assert "label" in definition
            assert "accept" in definition

    def test_allowed_extensions_known_category(self):
        """Vérifie les extensions pour une catégorie connue."""
        from apprenti.functions import _allowed_extensions
        
        extensions = _allowed_extensions("rapport")
        
        assert ".doc" in extensions or ".docx" in extensions

    def test_allowed_extensions_unknown_category(self):
        """Vérifie les extensions pour une catégorie inconnue."""
        from apprenti.functions import _allowed_extensions, DEFAULT_FILE_EXTENSIONS
        
        extensions = _allowed_extensions("unknown_category")
        
        assert extensions == DEFAULT_FILE_EXTENSIONS


class TestCompetencyDefinitions:
    """Tests pour les définitions de compétences."""

    def test_competency_definitions_exist(self):
        """Vérifie que les définitions existent."""
        from apprenti.functions import COMPETENCY_DEFINITIONS
        
        assert len(COMPETENCY_DEFINITIONS) > 0
        
        for competency in COMPETENCY_DEFINITIONS:
            assert "id" in competency
            assert "title" in competency
            assert "description" in competency

    def test_competency_levels_exist(self):
        """Vérifie que les niveaux existent."""
        from apprenti.functions import COMPETENCY_LEVELS
        
        assert len(COMPETENCY_LEVELS) > 0
        
        for level in COMPETENCY_LEVELS:
            assert "value" in level
            assert "label" in level


class TestListJournalDocuments:
    """Tests pour la liste des documents du journal."""

    @pytest.mark.asyncio
    async def test_list_documents_success(
        self, sample_apprenti_data, sample_promotion_data, mock_collection, async_cursor_factory
    ):
        """Vérifie la liste des documents."""
        from apprenti.functions import list_journal_documents
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
            
            result = await list_journal_documents(str(sample_apprenti_data["_id"]))
            
            assert "promotion" in result
            assert "semesters" in result
            assert "categories" in result


class TestSerializeDocument:
    """Tests pour la sérialisation des documents."""

    def test_serialize_document(self):
        """Vérifie la sérialisation d'un document."""
        from apprenti.functions import _serialize_document
        
        document = {
            "_id": ObjectId(),
            "semester_id": "S9",
            "category": "rapport",
            "file_name": "rapport.pdf",
            "file_size": 1024,
            "file_type": "application/pdf",
            "uploaded_at": datetime.utcnow(),
            "uploader": {
                "id": "user123",
                "name": "Jean Dupont",
                "role": "apprenti"
            },
            "comments": []
        }
        
        serialized = _serialize_document(document)
        
        assert "id" in serialized
        assert serialized["category"] == "rapport"
        assert serialized["file_name"] == "rapport.pdf"
        assert "download_url" in serialized


class TestHelperFunctions:
    """Tests pour les fonctions utilitaires."""

    def test_snake_to_camel_case(self):
        """Vérifie la conversion snake_case vers camelCase."""
        from apprenti.functions import _snake_to_camel_case
        
        assert _snake_to_camel_case("start_date") == "startDate"
        assert _snake_to_camel_case("semester_id") == "semesterId"
        assert _snake_to_camel_case("simple") == "simple"

    def test_parse_iso_date_valid(self):
        """Vérifie le parsing d'une date ISO valide."""
        from apprenti.functions import _parse_iso_date
        
        result = _parse_iso_date("2024-09-01")
        
        assert result is not None
        assert result.year == 2024
        assert result.month == 9
        assert result.day == 1

    def test_parse_iso_date_invalid(self):
        """Vérifie le parsing d'une date invalide."""
        from apprenti.functions import _parse_iso_date
        
        result = _parse_iso_date("invalid-date")
        
        assert result is None

    def test_parse_iso_date_none(self):
        """Vérifie le parsing de None."""
        from apprenti.functions import _parse_iso_date
        
        result = _parse_iso_date(None)
        
        assert result is None

    def test_normalize_semester_id(self):
        """Vérifie la normalisation des IDs de semestre."""
        from apprenti.functions import _normalize_semester_id
        
        assert _normalize_semester_id("S9") == "S9"
        assert _normalize_semester_id(None) == ""
        assert _normalize_semester_id(123) == "123"
