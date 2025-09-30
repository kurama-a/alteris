from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth.models import User, Token
from auth.service import hash_password, verify_password, create_access_token, decode_access_token
from common import db as database


#http://localhost:8005/auth/docs
auth_api = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@auth_api.post("/register")
async def register(user: User):
    # Vérifie si la DB est bien initialisée
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    # Vérifie si un utilisateur existe déjà
    existing = await database.db["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà.")

    # Hash du mot de passe
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)

    # Insertion en base
    result = await database.db["users"].insert_one(user_dict)
    return {"message": "Utilisateur enregistré", "id": str(result.inserted_id)}


@auth_api.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")

    # Recherche de l’utilisateur
    user = await database.db["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # Ici on ne renvoie pas le token, juste un message
    return {"message": "Connexion réussie"}


@auth_api.get("/me")
async def get_me(token: str = Depends(oauth2_scheme)):
    # Décodage du JWT
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return {"email": email}