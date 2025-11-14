from fastapi import APIRouter, HTTPException
from bson import ObjectId
import common.db as database
from tuteur.models import HealthResponse

tuteur_api = APIRouter(tags=["Tuteur"])

@tuteur_api.get("/profile")
def get_profile():
    return {"message": "Données du profil tuteur pédagogique"}

@tuteur_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "tuteur"}

# ✅ Infos complètes
@tuteur_api.get("/infos-completes/{tuteur_id}", tags=["Tuteur"])
async def get_tuteur_infos_completes(tuteur_id: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    col = database.db["users_tuteur_pedagogique"]
    doc = await col.find_one({"_id": ObjectId(tuteur_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Tuteur introuvable")
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