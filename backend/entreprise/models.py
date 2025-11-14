from pydantic import BaseModel, Field, EmailStr
from typing import Optional
class HealthResponse(BaseModel):
    status: str
    service: str


class Entity(BaseModel):
    raisonSociale: str = Field(..., example="Alteris Solutions")
    siret: str = Field(..., example="12345678900011")
    role: str = Field(..., example="entreprise_externe")  # ou "ecole"
    adresse: Optional[str] = Field(None, example="10 rue de Paris, 75000 Paris")
    email: EmailStr = Field(..., example="contact@alteris.fr")
    creeLe: Optional[str] = Field(None, example="2025-01-01")