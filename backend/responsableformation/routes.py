from fastapi import APIRouter, HTTPException
from bson import ObjectId
import common.db as database

from responsableformation.models import HealthResponse, User, UserUpdate
from functions import (
    creer_responsable_formation,
    mettre_a_jour_responsable_formation,
    supprimer_responsable_formation,
)

responsableformation_api = APIRouter(tags=["ResponsableFormation"])


@responsableformation_api.get("/profile")
def get_profile():
    return {"message": "Données du profil responsable de formation"}


@responsableformation_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "responsable_formation"}


@responsableformation_api.get("/infos-completes/{responsableformation_id}", tags=["ResponsableFormation"])
async def get_responsableformation_infos_completes(responsableformation_id: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    col = database.db["users_responsable_formation"]
    doc = await col.find_one({"_id": ObjectId(responsableformation_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Responsable de formation introuvable")
    return {
        "message": "Données récupérées avec succès",
        "data": {
            "_id": str(doc["_id"]),
            "first_name": doc.get("first_name"),
            "last_name": doc.get("last_name"),
            "email": doc.get("email"),
            "phone": doc.get("phone"),
        },
    }


@responsableformation_api.post("/", tags=["ResponsableFormation"])
async def create_responsableformation(payload: User):
    return await creer_responsable_formation(payload)


@responsableformation_api.put("/{responsableformation_id}", tags=["ResponsableFormation"])
async def update_responsableformation(responsableformation_id: str, payload: UserUpdate):
    return await mettre_a_jour_responsable_formation(responsableformation_id, payload)


@responsableformation_api.delete("/{responsableformation_id}", tags=["ResponsableFormation"])
async def delete_responsableformation(responsableformation_id: str):
    return await supprimer_responsable_formation(responsableformation_id)
