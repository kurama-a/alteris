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
    entreprise_externe = "entreprise_externe"
    ecole = "ecole"
    jury = "jury"
    professeur = "professeur"

# ✅ Schéma de requête
class User(BaseModel):
    first_name: str = Field(..., example="Fatou")
    last_name: str = Field(..., example="Diop")
    email: EmailStr = Field(..., example="fatou@example.com")
    phone: str = Field(..., example="+22912345678")
    password: str = Field(..., example="securePassword123")
    role: UserRole = Field(..., description="Rôle à choisir dans la liste")

class Entity(BaseModel):
    raisonSociale: str = Field(..., example="Alteris Solutions")
    siret: str = Field(..., example="12345678900011")
    role: UserRole = Field(..., example="entreprise_externe")
    adresse: Optional[str] = Field(None, example="10 rue de Paris, 75000 Paris")
    email: EmailStr = Field(..., example="contact@alteris.fr")
    creeLe: Optional[str] = Field(None, example="2025-01-01")



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