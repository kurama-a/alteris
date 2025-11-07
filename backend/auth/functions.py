from pydantic import BaseModel
import unicodedata
import string
import random
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict

from common import db as database
from auth.models import UserRole, User, LoginRequest, EmailRequest, PasswordRecoveryRequest

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

def decode_access_token(token: str) -> str | None:
    """
    Décode un JWT et retourne l'identifiant utilisateur ("sub") si valide.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
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

# =====================
# 🌍 Domaines par rôle
# =====================

DOMAINES_PAR_PROFIL = {
    "apprenti": "reseaualternance.fr",
    "tuteur_pedagogique": "tuteurs.reseaualternance.fr",
    "maitre_apprentissage": "maitre.reseaualternance.fr",
    "coordinatrice": "coordination.reseaualternance.fr",
    "entreprise_externe": "entreprise.reseaualternance.fr",
    "responsable_cursus": "cursus.reseaualternance.fr"
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
# LOGIN
# ------------------------
async def login_user(req: LoginRequest) -> Dict:
    """
    Recherche l'utilisateur dans chaque collection de rôles.
    Si trouvé et mot de passe valide -> retourne token et métadonnées.
    """
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    roles = [role.value for role in UserRole]
    for role in roles:
        collection = get_collection_from_role(role)
        user = await collection.find_one({"email": req.email})
        if user:
            if not verify_password(req.password, user.get("password", "")):
                raise HTTPException(status_code=401, detail="Mot de passe incorrect")

            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()

            access_token = create_access_token({
                "sub": user["email"],
                "role": role,
                "full_name": full_name
            })

            return {
                "message": "Connexion réussie",
                "access_token": access_token,
                "token_type": "bearer",
                "email": user["email"],
                "full_name": full_name,
                "role": role
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

    # Si decode_access_token renvoie juste l'email, on retourne email.
    # Si elle renvoie un dict (payload), on le retourne directement.
    return {"payload": payload}


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