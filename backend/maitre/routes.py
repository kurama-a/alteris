from fastapi import APIRouter, HTTPException
from bson import ObjectId
import common.db as database
from maitre.models import HealthResponse

maitre_api = APIRouter(tags=["Maitre Apprentissage"])

@maitre_api.get("/profile")
def get_profile():
    return {"message": "Profil maître d'apprentissage"}

@maitre_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "maitre_apprentissage"}

# ✅ Infos complètes
@maitre_api.get("/infos-completes/{maitre_id}", tags=["Maitre Apprentissage"])
async def get_maitre_infos_completes(maitre_id: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    col = database.db["users_maitre_apprentissage"]
    doc = await col.find_one({"_id": ObjectId(maitre_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Maître introuvable")
    return {
        "message": "✅ Données récupérées avec succès",
        "data": {
            "_id": str(doc["_id"]),
            "first_name": doc.get("first_name"),
            "last_name": doc.get("last_name"),
            "email": doc.get("email"),
            "phone": doc.get("phone"),
        }
    }