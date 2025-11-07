from fastapi import APIRouter, HTTPException
from bson import ObjectId
import common.db as database
from responsableformation.models import HealthResponse

responsableformation_api = APIRouter(tags=["ResponsableFormation"])

@responsableformation_api.get("/profile")
def get_profile():
    return {"message": "Données du profil responsable de formation"}

@responsableformation_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "responsableformation"}


# ✅ Infos complètes
@responsableformation_api.get("/infos-completes/{responsableformation_id}", tags=["ResponsableFormation"])
async def get_responsableformation_infos_completes(responsableformation_id: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    # NOTE: ajuster le nom de collection si besoin (ex: users_responsable_formation)
    col = database.db["users_responsableformation"]
    doc = await col.find_one({"_id": ObjectId(responsableformation_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Responsable de formation introuvable")
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