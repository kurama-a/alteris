"""
Tests unitaires pour le module Auth.
Tests des fonctions de sécurité, JWT et gestion des utilisateurs.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPasswordHashing:
    """Tests pour les fonctions de hachage de mot de passe."""

    def test_hash_password_creates_hash(self):
        """Vérifie que le hachage crée un hash différent du mot de passe."""
        from auth.functions import hash_password
        
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert "$" in hashed  # Format bcrypt

    def test_hash_password_different_for_same_input(self):
        """Vérifie que deux hachages du même mot de passe sont différents (sel)."""
        from auth.functions import hash_password
        
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Vérifie qu'un mot de passe correct est validé."""
        from auth.functions import hash_password, verify_password
        
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Vérifie qu'un mot de passe incorrect est rejeté."""
        from auth.functions import hash_password, verify_password
        
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword", hashed) is False


class TestJWTTokens:
    """Tests pour les fonctions de gestion JWT."""

    def test_create_access_token_from_dict(self):
        """Vérifie la création d'un token depuis un dictionnaire."""
        from auth.functions import create_access_token, decode_access_token
        
        data = {"sub": "test@example.com", "role": "apprenti"}
        token = create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
        
        decoded = decode_access_token(token)
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "apprenti"
        assert "exp" in decoded

    def test_create_access_token_from_string(self):
        """Vérifie la création d'un token depuis une chaîne."""
        from auth.functions import create_access_token, decode_access_token
        
        token = create_access_token("test@example.com")
        
        decoded = decode_access_token(token)
        assert decoded["sub"] == "test@example.com"

    def test_decode_access_token_valid(self):
        """Vérifie le décodage d'un token valide."""
        from auth.functions import create_access_token, decode_access_token
        
        data = {"sub": "test@example.com", "user_id": "12345"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == "12345"

    def test_decode_access_token_invalid(self):
        """Vérifie que le décodage échoue pour un token invalide."""
        from auth.functions import decode_access_token
        
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        
        assert decoded is None

    def test_decode_access_token_expired(self):
        """Vérifie que le décodage échoue pour un token expiré."""
        from jose import jwt
        from auth.functions import decode_access_token, SECRET_KEY, ALGORITHM
        
        expired_payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        decoded = decode_access_token(expired_token)
        assert decoded is None


class TestNormalize:
    """Tests pour la fonction de normalisation."""

    def test_normalize_removes_accents(self):
        """Vérifie que les accents sont supprimés."""
        from auth.functions import normalize
        
        assert normalize("éàùç") == "eauc"

    def test_normalize_removes_spaces(self):
        """Vérifie que les espaces sont supprimés."""
        from auth.functions import normalize
        
        assert normalize("Jean Dupont") == "jeandupont"

    def test_normalize_lowercase(self):
        """Vérifie que le texte est mis en minuscules."""
        from auth.functions import normalize
        
        assert normalize("JEAN") == "jean"

    def test_normalize_combined(self):
        """Vérifie la normalisation combinée."""
        from auth.functions import normalize
        
        assert normalize("Éloïse Du Pont") == "eloisedupont"


class TestGeneratePassword:
    """Tests pour la génération de mot de passe."""

    def test_generate_password_default_length(self):
        """Vérifie la longueur par défaut."""
        from auth.functions import generate_password
        
        password = generate_password()
        assert len(password) == 10

    def test_generate_password_custom_length(self):
        """Vérifie une longueur personnalisée."""
        from auth.functions import generate_password
        
        password = generate_password(length=15)
        assert len(password) == 15

    def test_generate_password_unique(self):
        """Vérifie que les mots de passe générés sont uniques."""
        from auth.functions import generate_password
        
        passwords = [generate_password() for _ in range(100)]
        # Tous devraient être uniques
        assert len(set(passwords)) == 100

    def test_generate_password_alphanumeric(self):
        """Vérifie que le mot de passe est alphanumérique."""
        from auth.functions import generate_password
        
        password = generate_password()
        assert password.isalnum()


class TestBuildMeFromDocument:
    """Tests pour la construction de l'objet 'me'."""

    def test_build_me_basic_fields(self):
        """Vérifie les champs de base."""
        from auth.functions import build_me_from_document
        
        user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
        }
        
        me = build_me_from_document(user, "apprenti")
        
        assert me["email"] == "test@example.com"
        assert me["fullName"] == "Jean Dupont"
        assert me["role"] == "apprenti"
        assert "id" in me

    def test_build_me_with_phone(self):
        """Vérifie l'inclusion du téléphone."""
        from auth.functions import build_me_from_document
        
        user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "phone": "+33612345678",
        }
        
        me = build_me_from_document(user, "apprenti")
        
        assert me.get("phone") == "+33612345678"

    def test_build_me_with_annee_academique(self):
        """Vérifie l'inclusion de l'année académique."""
        from auth.functions import build_me_from_document
        
        user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "annee_academique": "E5a",
        }
        
        me = build_me_from_document(user, "apprenti")
        
        assert me.get("anneeAcademique") == "E5a"

    def test_build_me_fallback_name(self):
        """Vérifie le nom de repli si first/last_name manquants."""
        from auth.functions import build_me_from_document
        
        user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "full_name": "Jean Dupont",
        }
        
        me = build_me_from_document(user, "apprenti")
        
        assert me["fullName"] == "Jean Dupont"


class TestGetCollectionNameByRole:
    """Tests pour la conversion rôle -> nom de collection."""

    def test_basic_role(self):
        """Vérifie la conversion d'un rôle simple."""
        from auth.functions import get_collection_name_by_role
        
        assert get_collection_name_by_role("apprenti") == "users_apprenti"

    def test_role_with_underscore(self):
        """Vérifie la conversion d'un rôle avec underscore."""
        from auth.functions import get_collection_name_by_role
        
        assert get_collection_name_by_role("tuteur_pedagogique") == "users_tuteur_pedagogique"

    def test_role_uppercase(self):
        """Vérifie la conversion d'un rôle en majuscules."""
        from auth.functions import get_collection_name_by_role
        
        assert get_collection_name_by_role("APPRENTI") == "users_apprenti"


class TestRegisterUser:
    """Tests pour l'enregistrement d'utilisateur."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, mock_collection):
        """Vérifie l'enregistrement réussi d'un utilisateur."""
        from auth.functions import register_user
        from auth.models import User, UserRole
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            user = User(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                phone="+33600000000",
                age=25,
                annee_academique="E5a",
                password="SecurePassword123",
                role=UserRole.apprenti
            )
            
            result = await register_user(user)
            
            assert result["message"] == "✅ Utilisateur enregistré avec succès"
            assert "user_id" in result
            assert result["role"] == "apprenti"

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, mock_collection):
        """Vérifie le rejet si l'email existe déjà."""
        from auth.functions import register_user
        from auth.models import User, UserRole
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value={"email": "test@example.com"})
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            user = User(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                phone="+33600000000",
                age=25,
                annee_academique="E5a",
                password="SecurePassword123",
                role=UserRole.apprenti
            )
            
            result = await register_user(user)
            
            # JSONResponse retournée
            assert result.status_code == 409


class TestLoginUser:
    """Tests pour la connexion utilisateur."""

    @pytest.mark.asyncio
    async def test_login_success(self, sample_apprenti_data, mock_collection):
        """Vérifie la connexion réussie."""
        from auth.functions import login_user, hash_password
        from auth.models import LoginRequest
        import common.db as database
        
        # Préparer le mot de passe hashé
        sample_apprenti_data["password"] = hash_password("password123")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = LoginRequest(
                email="jean.dupont@reseaualternance.fr",
                password="password123"
            )
            
            result = await login_user(req)
            
            assert result["message"] == "Connexion réussie"
            assert "access_token" in result
            assert result["token_type"] == "bearer"
            assert "me" in result

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, sample_apprenti_data, mock_collection):
        """Vérifie le rejet pour mot de passe incorrect."""
        from auth.functions import login_user, hash_password
        from auth.models import LoginRequest
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("correct_password")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = LoginRequest(
                email="jean.dupont@reseaualternance.fr",
                password="wrong_password"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await login_user(req)
            
            assert exc_info.value.status_code == 401
            assert "incorrect" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_collection):
        """Vérifie le rejet pour utilisateur non trouvé."""
        from auth.functions import login_user
        from auth.models import LoginRequest
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = LoginRequest(
                email="nonexistent@example.com",
                password="password123"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await login_user(req)
            
            assert exc_info.value.status_code == 404


class TestGetCurrentUser:
    """Tests pour la récupération de l'utilisateur courant."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, sample_apprenti_data, mock_collection):
        """Vérifie la récupération avec un token valide."""
        from auth.functions import get_current_user, create_access_token
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        token = create_access_token({
            "sub": "jean.dupont@reseaualternance.fr",
            "role": "apprenti"
        })
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await get_current_user(token)
            
            assert "me" in result
            assert result["me"]["email"] == "jean.dupont@reseaualternance.fr"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Vérifie le rejet avec un token invalide."""
        from auth.functions import get_current_user
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid.token.here")
        
        assert exc_info.value.status_code == 401


class TestGenerateEmailForRole:
    """Tests pour la génération d'email par rôle."""

    @pytest.mark.asyncio
    async def test_generate_email_apprenti(self, mock_collection):
        """Vérifie la génération d'email pour un apprenti."""
        from auth.functions import generate_email_for_role
        from auth.models import EmailRequest
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = EmailRequest(
                nom="Dupont",
                prenom="Jean",
                profil="apprenti"
            )
            
            result = await generate_email_for_role(req)
            
            assert result["email"] == "jean.dupont@reseaualternance.fr"
            assert "password" in result
            assert result["role"] == "apprenti"

    @pytest.mark.asyncio
    async def test_generate_email_tuteur(self, mock_collection):
        """Vérifie la génération d'email pour un tuteur."""
        from auth.functions import generate_email_for_role
        from auth.models import EmailRequest
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = EmailRequest(
                nom="Martin",
                prenom="Marie",
                profil="tuteur_pedagogique"
            )
            
            result = await generate_email_for_role(req)
            
            assert result["email"] == "marie.martin@tuteurs.reseaualternance.fr"
            assert result["role"] == "tuteur_pedagogique"


class TestRecoverPassword:
    """Tests pour la récupération de mot de passe."""

    @pytest.mark.asyncio
    async def test_recover_password_success(self, sample_apprenti_data, mock_collection):
        """Vérifie la récupération de mot de passe réussie."""
        from auth.functions import recover_password_for_role
        from auth.models import PasswordRecoveryRequest
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        mock_collection.update_one = AsyncMock()
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = PasswordRecoveryRequest(
                email="jean.dupont@reseaualternance.fr",
                profil="apprenti"
            )
            
            result = await recover_password_for_role(req)
            
            assert "new_password" in result
            assert result["email"] == "jean.dupont@reseaualternance.fr"

    @pytest.mark.asyncio
    async def test_recover_password_user_not_found(self, mock_collection):
        """Vérifie le rejet si l'utilisateur n'existe pas."""
        from auth.functions import recover_password_for_role
        from auth.models import PasswordRecoveryRequest
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            req = PasswordRecoveryRequest(
                email="nonexistent@example.com",
                profil="apprenti"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await recover_password_for_role(req)
            
            assert exc_info.value.status_code == 404


class TestUpdateCurrentUser:
    """Tests pour la mise à jour du profil utilisateur."""

    @pytest.mark.asyncio
    async def test_update_email_success(self, sample_apprenti_data, mock_collection):
        """Vérifie la mise à jour de l'email."""
        from auth.functions import update_current_user, create_access_token, hash_password
        from auth.models import UpdateMeRequest
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("password123")
        updated_user = {**sample_apprenti_data, "email": "nouveau@example.com"}
        
        # Créer un mock qui gère les différents appels
        call_count = [0]
        
        async def find_one_mock(query):
            call_count[0] += 1
            # Premier appel : récupérer utilisateur par email
            if call_count[0] == 1:
                return sample_apprenti_data
            # Vérifications email disponible (retourne None = disponible)
            # Dernier appel : récupérer utilisateur mis à jour après update
            if "_id" in query:
                return updated_user
            return None  # Email disponible
        
        mock_collection.find_one = find_one_mock
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        mock_collection.find = MagicMock(return_value=AsyncMock())
        
        token = create_access_token({
            "sub": "jean.dupont@reseaualternance.fr",
            "role": "apprenti"
        })
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UpdateMeRequest(
                email="nouveau@example.com",
                current_password="password123"
            )
            
            result = await update_current_user(token, payload)
            
            assert "Profil mis a jour" in result["message"]

    @pytest.mark.asyncio
    async def test_update_password_mismatch(self, sample_apprenti_data, mock_collection):
        """Vérifie le rejet si la confirmation ne correspond pas."""
        from auth.functions import update_current_user, create_access_token, hash_password
        from auth.models import UpdateMeRequest
        import common.db as database
        
        sample_apprenti_data["password"] = hash_password("password123")
        mock_collection.find_one = AsyncMock(return_value=sample_apprenti_data)
        
        token = create_access_token({
            "sub": "jean.dupont@reseaualternance.fr",
            "role": "apprenti"
        })
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            payload = UpdateMeRequest(
                new_password="NewPassword123",
                confirm_password="DifferentPassword123",
                current_password="password123"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await update_current_user(token, payload)
            
            assert exc_info.value.status_code == 400


class TestRegisterEntity:
    """Tests pour l'enregistrement d'entités."""

    @pytest.mark.asyncio
    async def test_register_entity_success(self, mock_collection):
        """Vérifie l'enregistrement réussi d'une entité."""
        from auth.functions import register_entity
        from auth.models import Entity
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            entity = Entity(
                raisonSociale="TechCorp",
                siret="12345678900011",
                email="contact@techcorp.fr",
                role="entreprise"
            )
            
            result = await register_entity(entity)
            
            assert "Entité enregistrée" in result["message"]
            assert result["role"] == "entreprise"

    @pytest.mark.asyncio
    async def test_register_entity_duplicate_siret(self, mock_collection, sample_entreprise_data):
        """Vérifie le rejet si le SIRET existe déjà."""
        from auth.functions import register_entity
        from auth.models import Entity
        import common.db as database
        
        mock_collection.find_one = AsyncMock(return_value=sample_entreprise_data)
        
        with patch.object(database, 'db', MagicMock()) as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            entity = Entity(
                raisonSociale="TechCorp",
                siret="12345678900011",
                email="autre@techcorp.fr",
                role="entreprise"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await register_entity(entity)
            
            assert exc_info.value.status_code == 409