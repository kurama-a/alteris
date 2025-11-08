from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    service: str

# 📄 Schéma de la requête
class AssocierTuteurRequest(BaseModel):
    apprenti_id: str
    tuteur_id: str

class AssocierResponsableRequest(BaseModel):
    apprenti_id: str
    responsable_id: str

class AssocierMaitreRequest(BaseModel):
    apprenti_id: str
    maitre_id: str

class AssocierCoordinatriceRequest(BaseModel):
    apprenti_id: str
    coordinatrice_id: str

class AssocierEntreprisesRequest(BaseModel):
    apprenti_id: str
    entreprise_id: str

class AssocierEcoleRequest(BaseModel):
    apprenti_id: str
    ecole_id: str


# class AssocierCoordinatriceRequest(BaseModel):
#     if UserRole == "apprenti":
#         apprenti_id: str
#         entreprise_id: str
#     if else UserRole == "maitre":
#         maitre_id: str
#         entreprise_id: str

