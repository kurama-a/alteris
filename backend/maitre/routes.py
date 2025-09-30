from fastapi import APIRouter
from maitre.models import HealthResponse

maitre_api = APIRouter(tags=["Maitre"])

@maitre_api.get("/profile")
def get_profile():
    return {"message": "Profil maître d'apprentissage"}

@maitre_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "maitre"}