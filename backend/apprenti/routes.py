from apprenti.models import HealthResponse, User
import common.db as database   # ← importer le module complet
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from .functions import recuperer_infos_apprenti_completes
apprenti_api = APIRouter(tags=["Apprenti"])

@apprenti_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "apprenti"}




# ✅ Infos complètes
@apprenti_api.get("/infos-completes/{apprenti_id}", tags=["Apprenti"])
async def get_apprenti_infos_completes(apprenti_id: str):
    return await recuperer_infos_apprenti_completes(apprenti_id)