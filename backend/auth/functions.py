auth/function.py 

import unicodedata
import string
import random
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from bson import ObjectId

from common import db as database
from auth.models import (
    UserRole,
    User,
    LoginRequest,
    EmailRequest,
    PasswordRecoveryRequest,
    Entity,
    UpdateMeRequest,
)
from auth.role_definitions import ROLE_DEFINITIONS, get_role_definition
from apprenti.functions import _build_journal_payload

# =====================
# 🔐 Sécurité & JWT
# =====================

# Clé secrète (à stocker dans une variable d’environnement en production)
SECRET_KEY = os.getenv("SECRET_KEY", "ton_secret_key_super_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Utilise bcrypt_sha256 pour éviter la limite de 72 octets de bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # supporte aussi bcrypt si besoin
    default="bcrypt_sha256",
    deprecated="auto",
)

def hash_password(password: str) -> str:
    """
    Hash le mot de passe avec bcrypt_sha256 (meilleur support des mots de passe longs).
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu’un mot de passe brut correspond à un hash.
    Tronque le mot de passe à 72 caractères si besoin.
    """
    MAX_LENGTH = 72
    # bcrypt accepte max 72 *octets*, pas caractères → mieux de tronquer manuellement
    truncated = plain_password.encode("utf-8")[:72].decode("utf-8", "ignore")
    return pwd_context.verify(truncated, hashed_password)

def create_access_token(data: dict | str) -> str:
    """
    Génère un JWT token avec expiration.
    """
    if isinstance(data, str):
        data = {"sub": data}

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode un JWT et retourne son payload si valide.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# =====================
# 🧠 Fonctions utilitaires
# =====================

def normalize(text: str) -> str:
    """
    Normalise une chaîne : supprime les accents, espaces, met en minuscule.
    Exemple : "Jean Dupont" -> "jeandupont"
    """
    return (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .replace(" ", "")
        .lower()
    )

def generate_password(length=10) -> str:
    """
    Génère un mot de passe aléatoire (lettres + chiffres).
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def build_me_from_document(user: Dict[str, Any], role: str) -> Dict[str, Any]:
    """
    Construit la structure « me » partagée avec le frontend à partir
    d'un document utilisateur stocké en base.
    """
    meta = get_role_definition(role)
    roles = meta.get("roles", [])
    role_label = meta.get("role_label")

    if not roles:
        roles = [role.replace("_", " ").title()]
    if not role_label:
        role_label = roles[0] if roles else role.replace("_", " ").title()

    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    if not full_name:
        full_name = user.get("full_name") or user.get("name") or user.get("email", "")

    me: Dict[str, Any] = {
        "id": str(user.get("_id") or user.get("id") or ""),
        "email": user.get("email", ""),
        "fullName": full_name,
        "roles": roles,
        "roleLabel": role_label,
        "role": role,
        "perms": meta.get("perms", []),
    }

    first_name = user.get("first_name")
    if isinstance(first_name, str) and first_name.strip():
        me["firstName"] = first_name.strip()

    last_name = user.get("last_name")
    if isinstance(last_name, str) and last_name.strip():
        me["lastName"] = last_name.strip()

    phone = user.get("phone")
    if isinstance(phone, str) and phone.strip():
        me["phone"] = phone.strip()

    stored_roles = user.get("roles")
    if isinstance(stored_roles, list) and stored_roles:
        me["roles"] = [str(item) for item in stored_roles]

    stored_role_label = user.get("roleLabel") or user.get("role_label")
    if isinstance(stored_role_label, str) and stored_role_label.strip():
        me["roleLabel"] = stored_role_label.strip()

    annee_academique = user.get("annee_academique") or user.get("anneeAcademique")
    if isinstance(annee_academique, str) and annee_academique.strip():
        me["anneeAcademique"] = annee_academique.strip()

    stored_perms = user.get("perms")
    if isinstance(stored_perms, list) and stored_perms:
        merged_perms = set(me["perms"])
        for perm in stored_perms:
            if isinstance(perm, str):
                merged_perms.add(perm)
        me["perms"] = sorted(merged_perms)

    optional_keys = (
        "profile",
        "company",
        "school",
        "tutors",
        "journalHeroImageUrl",
        "apprentices",
        "tuteur",
        "maitre",
    )
    for key in optional_keys:
        value = user.get(key)
        if value is not None:
            me[key] = value

    return me

# =====================
# 🌍 Domaines par rôle
# =====================

DOMAINES_PAR_PROFIL = {
    "apprenti": "reseaualternance.fr",
    "tuteur_pedagogique": "tuteurs.reseaualternance.fr",
    "maitre_apprentissage": "maitre.reseaualternance.fr",
    "coordinatrice": "coordination.reseaualternance.fr",
    "entreprise": "entreprise.reseaualternance.fr",
    "responsable_cursus": "cursus.reseaualternance.fr"
}

APPRENTICE_LINK_FIELDS = {
    "tuteur_pedagogique": "tuteur.tuteur_id",
    "maitre_apprentissage": "maitre.maitre_id",
    "entreprise": "company.entreprise_id",
}

# ------------------------
# Helpers DB / rôle
# ------------------------
def get_collection_name_by_role(role: str) -> str:
    """Normalise et retourne le nom de collection pour un rôle"""
    return f"users_{role.lower().replace(' ', '_')}"


def get_collection_from_role(role: str):
    """Retourne la collection MongoDB correspondante ou lève une erreur si DB non initialisée"""
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    return database.db[get_collection_name_by_role(role)]


def _all_known_roles() -> List[str]:
    roles = {role.value for role in UserRole}
    roles.update(ROLE_DEFINITIONS.keys())
    return list(roles)


async def fetch_supervised_apprentices(role: str, supervisor_id: ObjectId | str | None) -> List[Dict[str, Any]]:
    if database.db is None or supervisor_id is None:
        return []
    link_field = APPRENTICE_LINK_FIELDS.get(role)
    if not link_field:
        return []

    apprenti_collection = database.db["users_apprenti"]
    cursor = apprenti_collection.find({link_field: str(supervisor_id)})
    apprentices: List[Dict[str, Any]] = []
    async for apprenti in cursor:
        apprentices.append(_build_journal_payload(apprenti))
    return apprentices


async def enrich_me_with_apprentices(me: Dict[str, Any], role: str, user: Dict[str, Any]):
    apprentices = await fetch_supervised_apprentices(role, user.get("_id"))
    if apprentices:
        me["apprentices"] = apprentices
    elif "apprentices" in me:
        me.pop("apprentices", None)


# ------------------------
# REGISTER
# ------------------------
async def register_user(user: User) -> Dict:
    """Crée un utilisateur dans la collection correspondant à son rôle"""
    role = user.role.value
    collection = get_collection_from_role(role)

    existing_user = await collection.find_one({"email": user.email})
    if existing_user:
        return JSONResponse(status_code=409, content={"error": "Email déjà utilisé."})

    hashed_password = hash_password(user.password)

    user_doc = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "age": user.age,
        "annee_academique": user.annee_academique,
        "password": hashed_password,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await collection.insert_one(user_doc)

    return {
        "message": "✅ Utilisateur enregistré avec succès",
        "user_id": str(result.inserted_id),
        "role": role
    }

# ------------------------
# REGISTER ENTITY
# ------------------------
async def register_entity(entity: Entity) -> Dict[str, Any]:
    """Crée ou refuse une entité (ecole, entreprise, etc.)."""
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    collection = database.db["entities"]
    conflict_filter = {"$or": [{"siret": entity.siret}, {"email": entity.email}]}
    existing = await collection.find_one(conflict_filter)
    if existing:
        raise HTTPException(status_code=409, detail="Une entité avec ce SIRET ou cet email existe déjà")

    entity_doc = entity.dict()
    now = datetime.utcnow()
    entity_doc.update({"created_at": now, "updated_at": now})

    result = await collection.insert_one(entity_doc)
    return {
        "message": "Entité enregistrée avec succès",
        "entity_id": str(result.inserted_id),
        "role": entity.role,
    }
# ------------------------
# LOGIN
# ------------------------
async def login_user(req: LoginRequest) -> Dict:
    """
    Recherche l'utilisateur dans chaque collection de rôles.
    Si trouvé et mot de passe valide -> retourne token et métadonnées.
    """
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    roles: List[str] = [role.value for role in UserRole]
    for role_name in ROLE_DEFINITIONS.keys():
        if role_name not in roles:
            roles.append(role_name)

    for role in roles:
        collection = get_collection_from_role(role)
        user = await collection.find_one({"email": req.email})
        if user:
            hashed_password = user.get("password") or user.get("hashed_password", "")
            if not hashed_password:
                raise HTTPException(status_code=500, detail="Mot de passe non configuré")

            if not verify_password(req.password, hashed_password):
                raise HTTPException(status_code=401, detail="Mot de passe incorrect")

            me = build_me_from_document(user, role)
            if not me.get("email"):
                raise HTTPException(status_code=500, detail="Email utilisateur manquant")

            await enrich_me_with_apprentices(me, role, user)

            # Génération des notifications d'echeance pour l'utilisateur (si apprenti)
            try:
                from common.notifications import get_unread_notifications_for_user, generate_due_notifications_for_apprenti
                if role == "apprenti":
                    # create due-date notifications for this apprenti (best-effort, async helper)
                    try:
                        await generate_due_notifications_for_apprenti(user)
                    except Exception:
                        pass
                notifications = await get_unread_notifications_for_user(user.get("_id") and str(user.get("_id")) or user.get("_id") or user.get("email"))
            except Exception:
                notifications = []

            access_token = create_access_token(
                {
                    "sub": me["email"],
                    "role": role,
                    "user_id": me.get("id"),
                }
            )

            return {
                "message": "Connexion réussie",
                "access_token": access_token,
                "token_type": "bearer",
                "me": me,
                "notifications": notifications,
            }

    raise HTTPException(status_code=404, detail="Utilisateur non trouvé")


# ------------------------
# GET CURRENT USER (from token)
# ------------------------
async def get_current_user(token: str) -> Dict:
    """
    Decode le token et retourne l'email (ou payload si tu veux plus d'infos).
    Ici decode_access_token doit retourner l'email ou payload minimal.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    email = payload.get("sub")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=401, detail="Token incomplet")

    collection = get_collection_from_role(role)
    user = await collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    me = build_me_from_document(user, role)
    await enrich_me_with_apprentices(me, role, user)
    return {"me": me}


# ------------------------
# LIST USERS
# ------------------------
async def list_users() -> Dict[str, Any]:
    """
    Retourne la liste des utilisateurs connus, regroupés à travers les rôles.
    """
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    users: List[Dict[str, Any]] = []
    roles = {role.value for role in UserRole}
    roles.update(ROLE_DEFINITIONS.keys())

    for role in roles:
        collection = get_collection_from_role(role)
        cursor = collection.find()
        async for user in cursor:
            users.append(build_me_from_document(user, role))

    return {"users": users}


async def _ensure_email_available(email: str, exclude_user_id: ObjectId | None = None):
    """Verifie qu'aucun autre utilisateur n'utilise deja cet email."""
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisee")
    normalized_email = email.strip().lower()
    for role in _all_known_roles():
        collection = get_collection_from_role(role)
        existing = await collection.find_one({"email": normalized_email})
        if existing and (exclude_user_id is None or existing["_id"] != exclude_user_id):
            raise HTTPException(status_code=409, detail="Cet email est deja utilise par un autre utilisateur")


async def update_current_user(token: str, payload: UpdateMeRequest) -> Dict[str, Any]:
    payload_data = payload.dict(exclude_unset=True)
    desired_email = payload_data.get("email", None)
    desired_password = payload_data.get("new_password", None)
    confirm_password = payload_data.get("confirm_password", None)
    current_password = payload_data.get("current_password", None)

    if not desired_email and not desired_password:
        raise HTTPException(status_code=400, detail="Aucune modification demandee")

    payload_token = decode_access_token(token)
    if not payload_token:
        raise HTTPException(status_code=401, detail="Token invalide ou expire")

    role = payload_token.get("role")
    email = payload_token.get("sub")
    if not role or not email:
        raise HTTPException(status_code=401, detail="Token incomplet")

    collection = get_collection_from_role(role)
    user = await collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    hashed_password = user.get("password") or user.get("hashed_password")
    if (desired_password or (desired_email and desired_email.strip().lower() != email)) and not current_password:
        raise HTTPException(status_code=400, detail="Merci d'indiquer votre mot de passe actuel pour confirmer la modification")

    if current_password and not hashed_password:
        raise HTTPException(status_code=500, detail="Mot de passe actuel introuvable")

    if current_password and hashed_password and not verify_password(current_password, hashed_password):
        raise HTTPException(status_code=401, detail="Mot de passe actuel incorrect")

    updates: Dict[str, Any] = {}
    if desired_email:
        normalized_email = desired_email.strip().lower()
        if normalized_email != user.get("email"):
            await _ensure_email_available(normalized_email, user["_id"])
            updates["email"] = normalized_email

    if desired_password:
        if desired_password != confirm_password:
            raise HTTPException(status_code=400, detail="La confirmation du mot de passe ne correspond pas")
        updates["password"] = hash_password(desired_password)

    if not updates:
        raise HTTPException(status_code=400, detail="Aucune modification a appliquer")

    updates["updated_at"] = datetime.utcnow()
    await collection.update_one({"_id": user["_id"]}, {"$set": updates})

    updated_user = await collection.find_one({"_id": user["_id"]})
    me = build_me_from_document(updated_user, role)
    await enrich_me_with_apprentices(me, role, updated_user)

    return {"message": "Profil mis a jour avec succes", "me": me}


# ------------------------
# REGISTER ENTITY (ecole, entreprise)
# ------------------------
async def register_entity(entity: Entity) -> Dict:
    """Crée une entité dans la collection correspondant à son rôle (ecole, entreprise)."""
    role = entity.role.lower()
    if role not in {"ecole", "entreprise"}:
        raise HTTPException(status_code=400, detail="Rôle d'entité invalide (attendu: ecole ou entreprise)")

    collection = get_collection_from_role(role)

    # Conflit par siret ou email
    existing = await collection.find_one({"$or": [{"siret": entity.siret}, {"email": entity.email}]})
    if existing:
        raise HTTPException(status_code=409, detail="Entité déjà existante (même siret ou email)")

    doc = {
        "raisonSociale": entity.raisonSociale,
        "siret": entity.siret,
        "adresse": entity.adresse,
        "email": entity.email,
        "role": role,
        "creeLe": getattr(entity, "creeLe", None),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await collection.insert_one(doc)

    return {
        "message": "✅ Entité enregistrée avec succès",
        "entity_id": str(result.inserted_id),
        "role": role,
    }


# ------------------------
# GENERATE EMAIL
# ------------------------
async def generate_email_for_role(req: EmailRequest) -> Dict:
    """
    Génére un email institutionnel + mot de passe et injecte dans la collection du rôle.
    req.profil doit correspondre à un rôle existant comme 'apprenti', 'tuteur_pedagogique', etc.
    """
    role = req.profil.lower()
    collection = get_collection_from_role(role)

    prenom_clean = normalize(req.prenom)
    nom_clean = normalize(req.nom)
    domaine = DOMAINES_PAR_PROFIL.get(role, "reseaualternance.fr")
    email = f"{prenom_clean}.{nom_clean}@{domaine}"

    existing_user = await collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Un compte avec cet email existe déjà")

    password = generate_password()
    hashed_password = hash_password(password)

    await collection.insert_one({
        "first_name": req.prenom,
        "last_name": req.nom,
        "phone": getattr(req, "phone", None),
        "email": email,
        "password": hashed_password,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    return {
        "email": email,
        "password": password,
        "role": role
    }


# ------------------------
# RECOVER PASSWORD
# ------------------------
async def recover_password_for_role(req: PasswordRecoveryRequest) -> Dict:
    """
    Réinitialise le mot de passe pour un utilisateur existant dans la collection du rôle fourni.
    Retourne le nouveau mot de passe en clair (le hash est stocké).
    """
    role = req.profil.lower()
    collection = get_collection_from_role(role)

    user = await collection.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    new_password = generate_password()
    hashed_new = hash_password(new_password)

    await collection.update_one({"_id": user["_id"]}, {"$set": {"password": hashed_new, "updated_at": datetime.utcnow()}})

    return {
        "email": user["email"],
        "new_password": new_password,
        "message": f"Mot de passe réinitialisé pour {role}"
    }



