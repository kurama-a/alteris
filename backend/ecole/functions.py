from fastapi import HTTPException
from bson import ObjectId
import common.db as database

def get_collection(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[f"users_{role}"]

async def recuperer_infos_ecole_completes(ecole_id: str):
    """Récupère les informations complètes d'une école depuis la collection users_ecole."""
    try:
        ecole_collection = get_collection("ecole")

        # 🔍 Récupération de l’école
        ecole = await ecole_collection.find_one({"_id": ObjectId(ecole_id)})
        if not ecole:
            raise HTTPException(status_code=404, detail="École introuvable")

        # ✅ Structuration de la réponse
        infos = {
            "_id": str(ecole["_id"]),
            "raisonSociale": ecole.get("raisonSociale"),
            "siret": ecole.get("siret"),
            "adresse": ecole.get("adresse"),
            "email": ecole.get("email"),
            "creeLe": ecole.get("creeLe") or {}
        }

        return {
            "message": "✅ Données récupérées avec succès",
            "data": infos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")