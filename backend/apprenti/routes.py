from apprenti.models import HealthResponse, User
import common.db as database   # ← importer le module complet
from fastapi import APIRouter, HTTPException

# http://localhost:8001/apprenti/docs
apprenti_api = APIRouter(tags=["Apprenti"])

@apprenti_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "apprenti"}

