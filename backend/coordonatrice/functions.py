from bson import ObjectId
from fastapi import HTTPException

import common.db as database
from coordonatrice.models import User, UserUpdate


def get_collection():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db["users_coordonatrice"]


def serialize(document):
    if not document:
        return None
    return {
        "_id": str(document["_id"]),
        "first_name": document.get("first_name"),
        "last_name": document.get("last_name"),
        "email": document.get("email"),
        "phone": document.get("phone"),
        "role": document.get("role", "coordonatrice"),
    }


async def creer_coordonatrice(payload: User):
    collection = get_collection()
    document = payload.dict()
    document["role"] = document.get("role") or "coordonatrice"
    result = await collection.insert_one(document)
    created = await collection.find_one({"_id": result.inserted_id})
    return {"message": "Coordonatrice créée", "data": serialize(created)}


async def mettre_a_jour_coordonatrice(coordonatrice_id: str, payload: UserUpdate):
    collection = get_collection()
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await collection.update_one({"_id": ObjectId(coordonatrice_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coordonatrice introuvable")

    document = await collection.find_one({"_id": ObjectId(coordonatrice_id)})
    return {"message": "Coordonatrice mise à jour", "data": serialize(document)}


async def supprimer_coordonatrice(coordonatrice_id: str):
    collection = get_collection()
    result = await collection.delete_one({"_id": ObjectId(coordonatrice_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coordonatrice introuvable")
    return {"message": "Coordonatrice supprimée", "coordonatrice_id": coordonatrice_id}
