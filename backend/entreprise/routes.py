from entreprise.models import HealthResponse, Entity
import common.db as database   # ← importer le module complet
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from functions import recuperer_infos_entreprise_completes
entreprise_api = APIRouter(tags=["Entreprise"])

@entreprise_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "entreprise_externe"}

# (suppression de /info et /status, garder uniquement /health)

# ✅ Infos complètes
@entreprise_api.get("/infos-completes/{entreprise_id}", tags=["Entreprise Externe"])
async def get_entreprise_infos_completes(entreprise_id: str):
    return await recuperer_infos_entreprise_completes(entreprise_id)
