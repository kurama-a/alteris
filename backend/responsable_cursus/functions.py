from bson import ObjectId
from fastapi import HTTPException

import common.db as database
from responsable_cursus.models import User, UserUpdate


def get_collection():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db["users_responsable_cursus"]


def serialize(document):
    if not document:
        return None
    return {
        "_id": str(document["_id"]),
        "first_name": document.get("first_name"),
        "last_name": document.get("last_name"),
        "email": document.get("email"),
        "phone": document.get("phone"),
        "role": document.get("role", "responsable_cursus"),
    }


async def recuperer_infos_responsable_cursus_completes(responsable_cursus_id: str):
    try:
        collection = get_collection()
        responsable = await collection.find_one({"_id": ObjectId(responsable_cursus_id)})
        if not responsable:
            raise HTTPException(status_code=404, detail="Responsable cursus introuvable")

        return {
            "message": "Données récupérées avec succès",
            "data": serialize(responsable),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")


async def creer_responsable_cursus(payload: User):
    collection = get_collection()
    document = payload.dict()
    document["role"] = document.get("role") or "responsable_cursus"
    result = await collection.insert_one(document)
    created = await collection.find_one({"_id": result.inserted_id})
    return {"message": "Responsable cursus créé", "data": serialize(created)}


async def mettre_a_jour_responsable_cursus(responsable_cursus_id: str, payload: UserUpdate):
    collection = get_collection()
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await collection.update_one(
        {"_id": ObjectId(responsable_cursus_id)}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Responsable cursus introuvable")

    document = await collection.find_one({"_id": ObjectId(responsable_cursus_id)})
    return {"message": "Responsable cursus mis à jour", "data": serialize(document)}


async def supprimer_responsable_cursus(responsable_cursus_id: str):
    collection = get_collection()
    result = await collection.delete_one({"_id": ObjectId(responsable_cursus_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Responsable cursus introuvable")
    return {"message": "Responsable cursus supprimé", "responsable_cursus_id": responsable_cursus_id}
