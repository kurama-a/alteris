from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os

# Clé secrète (idéalement stockée dans une variable d’environnement)
SECRET_KEY = os.getenv("SECRET_KEY", "changeme123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Utiliser bcrypt_sha256 pour éviter la limite des 72 octets
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # supporte bcrypt pour compatibilité
    default="bcrypt_sha256",
    deprecated="auto",
)

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt_sha256 (sécurisé même si très long)."""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie qu’un mot de passe correspond au hash stocké."""
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: int = None) -> str:
    """Crée un JWT avec une date d’expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_delta or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    """Décode un JWT et retourne l’utilisateur (sub) si valide, sinon None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
