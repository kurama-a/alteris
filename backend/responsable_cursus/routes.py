from responsable_cursus.models import HealthResponse, User
import common.db as database   # ← importer le module complet
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from .functions import recuperer_infos_responsable_cursus_completes
responsable_cursus_api = APIRouter(tags=["responsable_cursus"])

@responsable_cursus_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "responsable_cursus"}




# ✅ Infos complètes
@responsable_cursus_api.get("/infos-completes/{responsable_cursus_id}", tags=["responsable_cursus"])
async def get_responsable_cursus_infos_completes(responsable_cursus_id: str):
    return await recuperer_infos_responsable_cursus_completes(responsable_cursus_id)