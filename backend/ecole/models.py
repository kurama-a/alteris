from pydantic import BaseModel, Field, EmailStr
from typing import Optional
class HealthResponse(BaseModel):
    status: str
    service: str



class Entity(BaseModel):
    raisonSociale: str = Field(..., example="Eseo")
    siret: str = Field(..., example="12345678900011")
    role: str = Field(..., example="ecole")  # ou "entreprise_externe"
    adresse: Optional[str] = Field(None, example="13 rue mauranne saulnier")
    email: EmailStr = Field(..., example="contact@eseo.fr")
    creeLe: Optional[str] = Field(None, example="2025-01-01")