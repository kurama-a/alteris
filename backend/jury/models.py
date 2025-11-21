from datetime import datetime
from enum import Enum
from typing import Optional

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
    semestre_reference: str = Field(..., description="Semestre concerné (E5a, S9...)")
    date: datetime = Field(..., description="Date et heure du passage du jury")
    status: JuryStatus = Field(default=JuryStatus.planifie, description="Statut du jury")


class JuryCreateRequest(JuryBase):
    tuteur_id: str = Field(..., description="ID du tuteur pédagogique")
    professeur_id: str = Field(..., description="ID du professeur (référent)")
    apprenti_id: str = Field(..., description="ID de l'apprenti présenté")
    intervenant_id: str = Field(..., description="ID de l'intervenant invité")


class JuryUpdateRequest(BaseModel):
    semestre_reference: Optional[str] = Field(None, description="Semestre concerné (E5a, S9...)")
    date: Optional[datetime] = Field(None, description="Date et heure du passage du jury")
    status: Optional[JuryStatus] = Field(None, description="Statut du jury")
    tuteur_id: Optional[str] = Field(None, description="Nouveau tuteur pédagogique")
    professeur_id: Optional[str] = Field(None, description="Nouveau professeur")
    apprenti_id: Optional[str] = Field(None, description="Nouvel apprenti")
    intervenant_id: Optional[str] = Field(None, description="Nouvel intervenant")


class JuryResponse(JuryBase):
    id: str = Field(..., description="Identifiant unique du jury")
    members: JuryMembers
    created_at: datetime
    updated_at: datetime
