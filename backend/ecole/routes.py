from ecole.models import HealthResponse, Entity
import common.db as database   # ← importer le module complet
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from functions import recuperer_infos_ecole_completes
ecole_api = APIRouter(tags=["Ecole"])

@ecole_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "ecole"}

# (suppression de /info et /status, garder uniquement /health)

# ✅ Infos complètes
@ecole_api.get("/infos-completes/{ecole_id}", tags=["Ecole"])
async def get_ecole_infos_completes(ecole_id: str):
    return await recuperer_infos_ecole_completes(ecole_id)