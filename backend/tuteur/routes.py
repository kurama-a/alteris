from fastapi import APIRouter
from tuteur.models import HealthResponse

tuteur_api = APIRouter(tags=["Tuteur"])

@tuteur_api.get("/profile")
def get_profile():
    return {"message": "Données du profil tuteur pédagogique"}

@tuteur_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "tuteur"}