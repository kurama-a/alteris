from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse

from auth.models import User, Entity, EmailRequest, PasswordRecoveryRequest, LoginRequest
import auth.functions as functions

auth_api = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@auth_api.post("/register", summary="Créer un nouvel utilisateur (collection par rôle)")
async def register(user: User):
    """Route légère : délègue la logique à functions.register_user"""
    return await functions.register_user(user)


@auth_api.post("/login", summary="Connexion par email (cherche dans chaque collection)")
async def login(req: LoginRequest):
    """Route légère : délègue la logique à functions.login_user"""
    return await functions.login_user(req)


@auth_api.post("/register-entity", summary="Créer une nouvelle entité (entreprise_externe, ecole, ...)")
async def register_entity(entity: Entity):
    """Route légère : délègue la logique à functions.register_entity"""
    return await functions.register_entity(entity)


@auth_api.get("/me", summary="Récupérer le profil depuis le token")
async def get_me(token: str = Depends(oauth2_scheme)):
    """Route légère : délègue la logique à functions.get_current_user"""
    return await functions.get_current_user(token)


@auth_api.get("/users", summary="Lister les utilisateurs agreges par role")
async def list_users():
    """Expose la liste des utilisateurs pour l'administration."""
    return await functions.list_users()


@auth_api.post("/generate-email", summary="Génère un email + mot de passe dans collection du rôle")
async def generate_email(req: EmailRequest):
    """Route légère : délègue la logique à functions.generate_email_for_role"""
    return await functions.generate_email_for_role(req)


@auth_api.post("/recover-password", summary="Réinitialise le mot de passe et le retourne")
async def recover_password(req: PasswordRecoveryRequest):
    """Route légère : délègue la logique à functions.recover_password_for_role"""
    return await functions.recover_password_for_role(req)
