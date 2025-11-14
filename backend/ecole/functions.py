from bson import ObjectId
from fastapi import HTTPException

import common.db as database
from ecole.models import Entity, EntityUpdate


def get_collection(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[f"users_{role}"]


def serialize(document):
    if not document:
        return None
    return {
        "_id": str(document["_id"]),
        "raisonSociale": document.get("raisonSociale"),
        "siret": document.get("siret"),
        "adresse": document.get("adresse"),
        "email": document.get("email"),
        "creeLe": document.get("creeLe"),
        "role": document.get("role", "ecole"),
    }


async def recuperer_infos_ecole_completes(ecole_id: str):
    try:
        ecole_collection = get_collection("ecole")
        ecole = await ecole_collection.find_one({"_id": ObjectId(ecole_id)})
        if not ecole:
            raise HTTPException(status_code=404, detail="École introuvable")

        return {
            "message": "Données récupérées avec succès",
            "data": serialize(ecole),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")


async def creer_ecole(payload: Entity):
    ecole_collection = get_collection("ecole")
    document = payload.dict()
    document["role"] = document.get("role") or "ecole"
    result = await ecole_collection.insert_one(document)
    created = await ecole_collection.find_one({"_id": result.inserted_id})
    return {"message": "École créée", "data": serialize(created)}


async def mettre_a_jour_ecole(ecole_id: str, payload: EntityUpdate):
    ecole_collection = get_collection("ecole")
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await ecole_collection.update_one({"_id": ObjectId(ecole_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="École introuvable")

    document = await ecole_collection.find_one({"_id": ObjectId(ecole_id)})
    return {"message": "École mise à jour", "data": serialize(document)}


async def supprimer_ecole(ecole_id: str):
    ecole_collection = get_collection("ecole")
    result = await ecole_collection.delete_one({"_id": ObjectId(ecole_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="École introuvable")
    return {"message": "École supprimée", "ecole_id": ecole_id}
