from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class User(BaseModel):
    name: str = Field(..., example="Jean Dupont")
    email: EmailStr = Field(..., example="jean.dupont@example.com")
    age: Optional[int] = Field(None, example=25)


class CreerEntretienRequest(BaseModel):
    apprenti_id: str
    date: datetime
    sujet: str


class DocumentDefinitionModel(BaseModel):
    id: str
    label: str
    description: str
    accept: str


class DocumentCommentModel(BaseModel):
    comment_id: str
    author_id: str
    author_name: str
    author_role: str
    content: str
    created_at: datetime


class JournalDocumentModel(BaseModel):
    id: str
    semester_id: str
    category: str
    file_name: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    uploader_id: str
    uploader_name: str
    uploader_role: str
    download_url: str
    comments: List[DocumentCommentModel] = Field(default_factory=list)


class SemesterDocumentsModel(BaseModel):
    semester_id: str
    name: str
    documents: List[JournalDocumentModel] = Field(default_factory=list)


class PromotionSummaryModel(BaseModel):
    promotion_id: str
    annee_academique: str
    label: Optional[str]


class ApprenticeDocumentsResponse(BaseModel):
    promotion: PromotionSummaryModel
    semesters: List[SemesterDocumentsModel]
    categories: List[DocumentDefinitionModel]


class DocumentUploadResponse(BaseModel):
    document: JournalDocumentModel


class DocumentCommentRequest(BaseModel):
    author_id: str
    author_name: str
    author_role: str
    content: str


class CompetencyDefinitionModel(BaseModel):
    id: str
    title: str
    description: list[str]


class CompetencyLevelModel(BaseModel):
    value: str
    label: str


class CompetencyEntryModel(BaseModel):
    competency_id: str
    level: Optional[str] = None


class SemesterCompetencyModel(BaseModel):
    semester_id: str
    name: str
    competencies: list[CompetencyEntryModel]


class ApprenticeCompetencyResponse(BaseModel):
    promotion: PromotionSummaryModel
    semesters: list[SemesterCompetencyModel]
    competencies: list[CompetencyDefinitionModel]
    levels: list[CompetencyLevelModel]


class CompetencyUpdateEntry(BaseModel):
    competency_id: str
    level: str


class CompetencyUpdateRequest(BaseModel):
    entries: list[CompetencyUpdateEntry]
