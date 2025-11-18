from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

# 🎯 Enum des rôles disponibles
class UserRole(str, Enum):
    apprenti = "apprenti"
    coordinatrice = "coordinatrice"
    responsable_cursus = "responsable_cursus"
    maitre_apprentissage = "maitre_apprentissage"
    tuteur_pedagogique = "tuteur_pedagogique"
    entreprise = "entreprise"
    admin = "administrateur"

# ✅ Schéma de requête
class User(BaseModel):
    first_name: str = Field(..., example="Fatou")
    last_name: str = Field(..., example="Diop")
    email: EmailStr = Field(..., example="fatou@example.com")
    phone: str = Field(..., example="+22912345678")
    age: int = Field(..., example="22")
    annee_academique: str = Field(..., example="E5a")    
    password: str = Field(..., example="securePassword123")
    role: UserRole = Field(..., description="Rôle à choisir dans la liste")

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None


class EmailRequest(BaseModel):
    nom: str
    prenom: str
    profil: str


class PasswordRecoveryRequest(BaseModel):
    email: str
    profil: str

 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateMeRequest(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = Field(
        default=None, description="Mot de passe actuel pour confirmer les modifications"
    )
    new_password: Optional[str] = Field(
        default=None,
        description="Nouveau mot de passe",
        min_length=8,
    )
    confirm_password: Optional[str] = Field(
        default=None,
        description="Confirmation du nouveau mot de passe",
    )

class Entity(BaseModel):
    raisonSociale: str = Field(..., example="Eseo")
    siret: str = Field(..., example="12345678900011")
    role: str = Field(..., example="ecole")
    adresse: Optional[str] = Field(None, example="13 rue mauranne saulnier")
    email: EmailStr = Field(..., example="contact@eseo.fr")
    creeLe: Optional[str] = Field(None, example="2025-01-01")

