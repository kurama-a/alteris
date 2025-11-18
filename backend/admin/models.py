from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class HealthResponse(BaseModel):
    status: str
    service: str

# 📄 Schéma de la requête
class AssocierTuteurRequest(BaseModel):
    apprenti_id: str
    tuteur_id: str
    
class AssocierResponsableCursusRequest(BaseModel):
    apprenti_id: str
    responsable_cursus_id: str

class AssocierResponsablePromoRequest(BaseModel):
    promo_annee_academique: str  # Exemple : "E5a", "2024-2025", etc.
    responsable_id: str
    
class AssocierMaitreRequest(BaseModel):
    apprenti_id: str = Field(..., description="ID de l'apprenti à associer")
    maitre_id: str = Field(..., description="ID du maître d'apprentissage à associer")

class PromotionUpsertRequest(BaseModel):
    annee_academique: str = Field(..., description="Identifiant de la promotion (ex: 2024-2025)")
    label: Optional[str] = Field(None, description="Libellé lisible de la promotion")
    coordinators: List[str] = Field(default_factory=list, description="Liste des coordinateurs (texte libre)")
    next_milestone: Optional[str] = Field(None, description="Prochaine échéance ou jalon important")
    responsable_id: Optional[str] = Field(None, description="ID du responsable de cursus à associer")

class AssocierEntrepriseRequest(BaseModel):
    apprenti_id: str = Field(..., description="ID de l'apprenti � associer")
    entreprise_id: str = Field(..., description="ID de l'entreprise � associer")

class AssocierJuryRequest(BaseModel):
    apprenti_id: str = Field(..., description="ID de l'apprenti à associer")
    professeur_id: str = Field(..., description="ID du professeur à copier en jury")

class UserUpdateModel(BaseModel):
    first_name: Optional[str] = Field(None, example="Ali")
    last_name: Optional[str] = Field(None, example="Bamba")
    email: Optional[EmailStr] = Field(None, example="ali.bamba@example.com")
    phone: Optional[str] = Field(None, example="0601020304")
