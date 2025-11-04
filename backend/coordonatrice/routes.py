from fastapi import APIRouter
from coordonatrice.models import HealthResponse

coordonatrice_api = APIRouter(tags=["Coordonatrice"])

@coordonatrice_api.get("/profile")
def get_profile():
    return {"message": "Données du profil coordonatrice"}

@coordonatrice_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "coordonatrice"}