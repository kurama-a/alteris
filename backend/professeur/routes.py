from fastapi import APIRouter, HTTPException
from bson import ObjectId
import common.db as database
from professeur.models import HealthResponse

professeur_api = APIRouter(tags=["Professeur"])

@professeur_api.get("/profile")
def get_profile():
    return {"message": "Données du profil professeur"}

@professeur_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "professeur"}

# ✅ Infos complètes
@professeur_api.get("/infos-completes/{professeur_id}", tags=["Professeur"])
async def get_professeur_infos_completes(professeur_id: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    col = database.db["users_professeur"]
    doc = await col.find_one({"_id": ObjectId(professeur_id)})
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