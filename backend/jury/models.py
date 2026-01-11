from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class JuryStatus(str, Enum):
    planifie = "planifie"
    termine = "termine"


class MemberDetails(BaseModel):
    user_id: str = Field(..., description="Identifiant unique de l'utilisateur")
    role: str = Field(..., description="Rôle de l'utilisateur dans la plateforme")
    first_name: Optional[str] = Field(None, example="Jeanne")
    last_name: Optional[str] = Field(None, example="Martin")
    email: Optional[EmailStr] = Field(None, example="jeanne.martin@example.com")
    phone: Optional[str] = Field(None, example="+33102030405")


class JuryMembers(BaseModel):
    tuteur: MemberDetails
    professeur: MemberDetails
    apprenti: MemberDetails
    intervenant: MemberDetails


class JuryBase(BaseModel):
    date: datetime = Field(..., description="Date et heure du passage du jury")
    status: JuryStatus = Field(default=JuryStatus.planifie, description="Statut du jury")
    note: Optional[float] = Field(None, description="Note du jury (0-20)")


class JuryCreateRequest(JuryBase):
    promotion_id: str = Field(..., description="ID de la promotion liée")
    semester_id: str = Field(..., description="ID du semestre concerné")
    tuteur_id: str = Field(..., description="ID du tuteur pédagogique")
    professeur_id: str = Field(..., description="ID du professeur (référent)")
    apprenti_id: str = Field(..., description="ID de l'apprenti présenté")
    intervenant_id: str = Field(..., description="ID de l'intervenant invité")


class JuryUpdateRequest(BaseModel):
    promotion_id: Optional[str] = Field(None, description="ID de la promotion liée")
    semester_id: Optional[str] = Field(None, description="ID du semestre concerné")
    date: Optional[datetime] = Field(None, description="Date et heure du passage du jury")
    status: Optional[JuryStatus] = Field(None, description="Statut du jury")
    note: Optional[float] = Field(None, description="Note du jury (0-20)")
    tuteur_id: Optional[str] = Field(None, description="Nouveau tuteur pédagogique")
    professeur_id: Optional[str] = Field(None, description="Nouveau professeur")
    apprenti_id: Optional[str] = Field(None, description="Nouvel apprenti")
    intervenant_id: Optional[str] = Field(None, description="Nouvel intervenant")


class JuryPromotionReference(BaseModel):
    promotion_id: str = Field(..., description="ID de la promotion liée")
    annee_academique: Optional[str] = Field(None, description="Année académique")
    label: Optional[str] = Field(None, description="Libellé de la promotion")
    semester_id: str = Field(..., description="ID du semestre")
    semester_name: str = Field(..., description="Nom du semestre")

    class Config:
        extra = "ignore"


class JuryResponse(JuryBase):
    semestre_reference: str = Field(..., description="Semestre de référence affiché")
    id: str = Field(..., description="Identifiant unique du jury")
    members: JuryMembers
    created_at: datetime
    updated_at: datetime
    promotion_reference: Optional[JuryPromotionReference] = Field(
        None, description="Référence promotion/semestre associée"
    )


class TimelineSemesterOption(BaseModel):
    semester_id: str = Field(..., description="ID du semestre")
    name: str = Field(..., description="Nom du semestre")


class JuryPromotionTimelineOption(BaseModel):
    promotion_id: str = Field(..., description="ID de la promotion")
    annee_academique: str = Field(..., description="Année académique de la promotion")
    label: Optional[str] = Field(None, description="Libellé de la promotion")
    semesters: List[TimelineSemesterOption] = Field(default_factory=list)
