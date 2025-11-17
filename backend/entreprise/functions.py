from bson import ObjectId
from fastapi import HTTPException

import common.db as database
from entreprise.models import Entity, EntityUpdate


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
        "role": document.get("role", "entreprise"),
    }


async def lister_entreprises():
    collection = get_collection("entreprise")
    entreprises = []
    cursor = collection.find().sort("raisonSociale", 1)
    async for document in cursor:
        entreprises.append(serialize(document))
    return {"entreprises": entreprises}


async def recuperer_infos_entreprise_completes(entreprise_id: str):
    try:
        entreprise_collection = get_collection("entreprise")
        entreprise = await entreprise_collection.find_one({"_id": ObjectId(entreprise_id)})
        if not entreprise:
            raise HTTPException(status_code=404, detail="Entreprise externe introuvable")

        return {
            "message": "Données récupérées avec succès",
            "data": serialize(entreprise),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")


async def creer_entreprise(payload: Entity):
    try:
        entreprise_collection = get_collection("entreprise")
        document = payload.dict()
        document["role"] = document.get("role") or "entreprise"
        result = await entreprise_collection.insert_one(document)
        created = await entreprise_collection.find_one({"_id": result.inserted_id})
        return {"message": "Entreprise créée", "data": serialize(created)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")


async def mettre_a_jour_entreprise(entreprise_id: str, payload: EntityUpdate):
    entreprise_collection = get_collection("entreprise")
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await entreprise_collection.update_one(
        {"_id": ObjectId(entreprise_id)}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entreprise externe introuvable")

    document = await entreprise_collection.find_one({"_id": ObjectId(entreprise_id)})
    return {"message": "Entreprise mise à jour", "data": serialize(document)}


async def supprimer_entreprise(entreprise_id: str):
    entreprise_collection = get_collection("entreprise")
    result = await entreprise_collection.delete_one({"_id": ObjectId(entreprise_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entreprise externe introuvable")
    return {"message": "Entreprise supprimée", "entreprise_id": entreprise_id}
