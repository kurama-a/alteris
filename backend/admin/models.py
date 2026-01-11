from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class HealthResponse(BaseModel):
    status: str
    service: str


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
    apprenti_id: str = Field(..., description="ID de l'apprenti a associer")
    maitre_id: str = Field(..., description="ID du maitre d'apprentissage a associer")


class PromotionDeliverablePayload(BaseModel):
    deliverable_id: Optional[str] = Field(
        None,
        alias="id",
        description="Identifiant du livrable si deja existant",
    )
    title: str = Field(..., description="Titre du livrable")
    due_date: Optional[str] = Field(None, description="Date d'echeance au format ISO (AAAA-MM-JJ)")
    description: Optional[str] = Field(None, description="Description libre")
    order: Optional[int] = Field(None, description="Ordre d'affichage optionnel")

    class Config:
        allow_population_by_field_name = True


class PromotionSemesterPayload(BaseModel):
    semester_id: Optional[str] = Field(
        None,
        alias="id",
        description="Identifiant du semestre si deja existant",
    )
    name: str = Field(..., description="Nom du semestre (ex: S9)")
    start_date: Optional[str] = Field(None, description="Date de debut (ISO, optionnel)")
    end_date: Optional[str] = Field(None, description="Date de fin (ISO, optionnel)")
    order: Optional[int] = Field(None, description="Ordre du semestre")
    deliverables: List[PromotionDeliverablePayload] = Field(
        default_factory=list,
        description="Livrables associes au semestre",
    )

    class Config:
        allow_population_by_field_name = True


class PromotionUpsertRequest(BaseModel):
    annee_academique: str = Field(..., description="Identifiant de la promotion (ex: 2024-2025)")
    label: Optional[str] = Field(None, description="Libelle lisible de la promotion")
    coordinators: List[str] = Field(default_factory=list, description="Liste des coordinateurs (texte libre)")
    next_milestone: Optional[str] = Field(None, description="Prochaine echeance ou jalon important")
    responsable_id: Optional[str] = Field(None, description="ID du responsable de cursus a associer")
    semesters: Optional[List[PromotionSemesterPayload]] = Field(
        None,
        description="Temporalite de la promotion (semestres et livrables)",
    )


class AssocierEntrepriseRequest(BaseModel):
    apprenti_id: str = Field(..., description="ID de l'apprenti a associer")
    entreprise_id: str = Field(..., description="ID de l'entreprise a associer")


class AssocierJuryRequest(BaseModel):
    apprenti_id: str = Field(..., description="ID de l'apprenti a associer")
    professeur_id: str = Field(..., description="ID du professeur a copier en jury")


class UserUpdateModel(BaseModel):
    first_name: Optional[str] = Field(None, example="Ali")
    last_name: Optional[str] = Field(None, example="Bamba")
    email: Optional[EmailStr] = Field(None, example="ali.bamba@example.com")
    phone: Optional[str] = Field(None, example="0601020304")

class PromotionTimelineRequest(BaseModel):
    semesters: List[PromotionSemesterPayload] = Field(
        default_factory=list,
        description="Temporalite complete de la promotion",
    )
