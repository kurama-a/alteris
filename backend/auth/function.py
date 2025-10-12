from pydantic import BaseModel
import unicodedata
import string
import random
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os

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