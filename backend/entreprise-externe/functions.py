from fastapi import HTTPException
from bson import ObjectId
import common.db as database

def get_collection(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[f"users_{role}"]

async def recuperer_infos_entreprise_completes(entreprise_id: str):
    try:
        entreprise_collection = get_collection("entreprise_externe")

        # 🔍 Récupération de l’entreprise externe
        entreprise = await entreprise_collection.find_one({"_id": ObjectId(entreprise_id)})
        if not entreprise:
            raise HTTPException(status_code=404, detail="Entreprise externe introuvable")

        # ✅ Structuration de la réponse
        infos = {
            "_id": str(entreprise["_id"]),
            "raisonSociale": entreprise.get("raisonSociale"),
            "siret": entreprise.get("siret"),
            "adresse": entreprise.get("adresse"),
            "email": entreprise.get("email"),
            "creeLe": entreprise.get("creeLe") or {}
        }

        return {
            "message": "✅ Données récupérées avec succès",
            "data": infos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")