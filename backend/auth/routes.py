from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import unicodedata
import string
import random
from auth.function import DOMAINES_PAR_PROFIL,normalize,generate_password,hash_password, verify_password, create_access_token, decode_access_token
from auth.models import User, Token, EmailRequest,PasswordRecoveryRequest,LoginRequest
from common import db as database
auth_api = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# =============================
# ✅ ROUTES 
# =============================

@auth_api.post("/register")
async def register(user: User):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    existing = await database.db["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà.")
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    result = await database.db["users"].insert_one(user_dict)
    return {"message": "Utilisateur enregistré", "id": str(result.inserted_id)}




@auth_api.post("/login")
async def login(req: LoginRequest):
    """
    Authentifie un utilisateur selon son profil et génère un token JWT personnalisé.
    """
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    # Profil normalisé et collection dynamique
    profil_clean = req.profil.lower().replace(" ", "_")
    collection_name = f"users_{profil_clean}"
    collection = database.db[collection_name]

    # Vérifie si l'utilisateur existe
    user = await collection.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans ce profil")

    # Vérifie le mot de passe
    if not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # ✅ Génère le token JWT avec email et profil
    access_token = create_access_token({
        "sub": user["email"],   # email de l'utilisateur
        "profil": profil_clean  # profil pour personnalisation front-end
    })

    # ✅ Retourne une réponse claire pour le front
    return {
        "message": "Connexion réussie",
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"],
        "profil": profil_clean
    }

@auth_api.get("/me")
async def get_me(token: str = Depends(oauth2_scheme)):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return {"email": email}



# =============================
# ✅ ROUTE : /generate-email
# =============================

@auth_api.post("/generate-email")
async def generate_email(req: EmailRequest):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    profil = req.profil.lower()
    domaine = DOMAINES_PAR_PROFIL.get(profil, "reseaualternance.fr")
    prenom_clean = normalize(req.prenom)
    nom_clean = normalize(req.nom)
    email = f"{prenom_clean}.{nom_clean}@{domaine}"

    password = generate_password()
    hashed_password = hash_password(password)

    collection_name = f"users_{profil}"
    collection = database.db[collection_name]

    existing_user = await collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Un compte avec cet email existe déjà")

    await collection.insert_one({
        "email": email,
        "password": hashed_password
    })

    return {
        "email": email,
        "password": password,
        "profil": profil
    }

# =============================
# ✅ ROUTE : /recover-password
# =============================



@auth_api.post("/recover-password")
async def recover_password(req: PasswordRecoveryRequest):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    profil = req.profil.lower()
    collection_name = f"users_{profil}"
    collection = database.db[collection_name]

    user = await collection.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    return {
        "email": user["email"],
        "password": user["password"]  # ⚠️ Si tu veux retourner le mot de passe en clair, ne le hashe pas dans /generate-email
    }