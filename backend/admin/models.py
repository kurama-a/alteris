from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    service: str

# 📄 Schéma de la requête
class AssocierTuteurRequest(BaseModel):
    apprenti_id: str
    tuteur_id: str
    
class AssocierMaitreRequest(BaseModel):
    apprenti_id: str
    maitre_id: str

class AssocierResponsableCursusRequest(BaseModel):
    apprenti_id: str
    responsable_cursus_id: str

class AssocierResponsablePromoRequest(BaseModel):
    promo_annee_academique: str  # Exemple : "E5a", "2024-2025", etc.
    responsable_id: str

class UserUpdateModel(BaseModel):
    first_name: Optional[str] = Field(None, example="Ali")
    last_name: Optional[str] = Field(None, example="Bamba")
    email: Optional[EmailStr] = Field(None, example="ali.bamba@example.com")
    phone: Optional[str] = Field(None, example="0601020304")