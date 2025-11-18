from fastapi import APIRouter, HTTPException
from bson import ObjectId
import common.db as database
from jury.models import HealthResponse

jury_api = APIRouter(tags=["Jury"])

@jury_api.get("/profile")
def get_profile():
    return {"message": "Données du profil jury"}
@jury_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "jury"}

# ✅ Infos complètes
@jury_api.get("/infos-completes/{jury_id}", tags=["Jury"])
async def get_jury_infos_completes(jury_id: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    col = database.db["users_jury"]
    doc = await col.find_one({"_id": ObjectId(jury_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Jury introuvable")
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