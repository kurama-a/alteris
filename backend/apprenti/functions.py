from fastapi import HTTPException
from bson import ObjectId
import common.db as database

def get_collection(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[f"users_{role}"]

async def recuperer_infos_apprenti_completes(apprenti_id: str):
    try:
        apprenti_collection = get_collection("apprenti")

        # 🔍 Récupération de l’apprenti
        apprenti = await apprenti_collection.find_one({"_id": ObjectId(apprenti_id)})
        if not apprenti:
            raise HTTPException(status_code=404, detail="Apprenti introuvable")

        # ✅ Structuration de la réponse
        infos = {
            "_id": str(apprenti["_id"]),
            "first_name": apprenti.get("first_name"),
            "last_name": apprenti.get("last_name"),
            "email": apprenti.get("email"),
            "phone": apprenti.get("phone"),
            "tuteur": apprenti.get("tuteur") or {}
        }

        return {
            "message": "✅ Données récupérées avec succès",
            "data": infos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")