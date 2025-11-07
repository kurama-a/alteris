from pydantic import BaseModel, Field, EmailStr
from typing import Optional

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

