from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from auth.models import (
    User,
    Entity,
    EmailRequest,
    PasswordRecoveryRequest,
    LoginRequest,
    UpdateMeRequest,
)
import auth.functions as functions

auth_api = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@auth_api.post("/register", summary="Creer un nouvel utilisateur (collection par role)")
async def register(user: User):
    """Delegue la creation a functions.register_user."""
    return await functions.register_user(user)


@auth_api.post("/login", summary="Connexion par email (cherche dans chaque collection)")
async def login(req: LoginRequest):
    """Delegue la logique a functions.login_user."""
    return await functions.login_user(req)


@auth_api.post("/register-entity", summary="Creer une nouvelle entite (entreprise, ecole, ...)")
async def register_entity(entity: Entity):
    """Delegue la logique a functions.register_entity."""
    return await functions.register_entity(entity)


@auth_api.get("/me", summary="Recuperer le profil depuis le token")
async def get_me(token: str = Depends(oauth2_scheme)):
    """Delegue la logique a functions.get_current_user."""
    return await functions.get_current_user(token)


@auth_api.patch("/me", summary="Mettre a jour le profil authentifie")
async def update_me(data: UpdateMeRequest, token: str = Depends(oauth2_scheme)):
    """Permet a l'utilisateur de modifier son email ou son mot de passe."""
    return await functions.update_current_user(token, data)


@auth_api.get("/users", summary="Lister les utilisateurs agreges par role")
async def list_users():
    """Expose la liste des utilisateurs pour l'administration."""
    return await functions.list_users()


@auth_api.post("/generate-email", summary="Genere un email + mot de passe dans la collection du role")
async def generate_email(req: EmailRequest):
    """Delegue la logique a functions.generate_email_for_role."""
    return await functions.generate_email_for_role(req)


@auth_api.post("/recover-password", summary="Reinitialise le mot de passe et le retourne")
async def recover_password(req: PasswordRecoveryRequest):
    """Delegue la logique a functions.recover_password_for_role."""
    return await functions.recover_password_for_role(req)
