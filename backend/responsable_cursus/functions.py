from fastapi import HTTPException
from bson import ObjectId
import common.db as database

def get_collection(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[f"users_{role}"]

async def recuperer_infos_responsable_cursus_completes(responsable_cursus_id: str):
    try:
        responsable_cursus_collection = get_collection("responsable_cursus")

        # 🔍 Récupération de l’responsable_cursus
        responsable_cursus = await responsable_cursus_collection.find_one({"_id": ObjectId(responsable_cursus_id)})
        if not responsable_cursus:
            raise HTTPException(status_code=404, detail="responsable_cursus introuvable")

        # ✅ Structuration de la réponse
        infos = {
            "_id": str(responsable_cursus["_id"]),
            "first_name": responsable_cursus.get("first_name"),
            "last_name": responsable_cursus.get("last_name"),
            "email": responsable_cursus.get("email"),
            "phone": responsable_cursus.get("phone"),
 #           "tuteur": responsable_cursus.get("tuteur") or {}
        }

        return {
            "message": "✅ Données récupérées avec succès",
            "data": infos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")