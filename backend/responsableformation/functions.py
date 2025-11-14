from bson import ObjectId
from fastapi import HTTPException

import common.db as database
from responsableformation.models import User, UserUpdate


def get_collection():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db["users_responsable_formation"]


def serialize(document):
    if not document:
        return None
    return {
        "_id": str(document["_id"]),
        "first_name": document.get("first_name"),
        "last_name": document.get("last_name"),
        "email": document.get("email"),
        "phone": document.get("phone"),
        "role": document.get("role", "responsable_formation"),
    }


async def creer_responsable_formation(payload: User):
    collection = get_collection()
    document = payload.dict()
    document["role"] = document.get("role") or "responsable_formation"
    result = await collection.insert_one(document)
    created = await collection.find_one({"_id": result.inserted_id})
    return {"message": "Responsable formation créé", "data": serialize(created)}


async def mettre_a_jour_responsable_formation(responsable_id: str, payload: UserUpdate):
    collection = get_collection()
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await collection.update_one({"_id": ObjectId(responsable_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Responsable formation introuvable")

    document = await collection.find_one({"_id": ObjectId(responsable_id)})
    return {"message": "Responsable formation mis à jour", "data": serialize(document)}


async def supprimer_responsable_formation(responsable_id: str):
    collection = get_collection()
    result = await collection.delete_one({"_id": ObjectId(responsable_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Responsable formation introuvable")
    return {"message": "Responsable formation supprimé", "responsableformation_id": responsable_id}
