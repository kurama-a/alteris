from fastapi import HTTPException
from datetime import datetime
import common.db as database
from bson import ObjectId
from models import UserUpdateModel


ROLES_VALIDES = ["apprenti", "tuteur_pedagogique", "coordinatrice", "responsable_cursus"]

async def get_apprentis_by_annee_academique(annee_academique: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection_apprenti = database.db["users_apprenti"]
    collection_promo = database.db["promos"]

    # 🔍 Étape 1 : Récupérer tous les apprentis de cette année académique
    apprentis_meme_promo = await collection_apprenti.find(
        {"annee_academique": annee_academique}
    ).to_list(length=None)

    if not apprentis_meme_promo:
        raise HTTPException(status_code=404, detail="Aucun apprenti trouvé pour cette année académique")

    # 🗂️ Étape 2 : Construire le document de promo
    promo_doc = {
        "annee_academique": annee_academique,
        "nb_apprentis": len(apprentis_meme_promo),
        "created_at": datetime.utcnow(),
        "apprentis": [{
            "_id": str(apprenti["_id"]),
            "first_name": apprenti.get("first_name"),
            "last_name": apprenti.get("last_name"),
            "email": apprenti.get("email"),
            "phone": apprenti.get("phone")
        } for apprenti in apprentis_meme_promo]
    }

    # 💾 Étape 3 : Créer ou mettre à jour la promo
    await collection_promo.update_one(
        {"annee_academique": annee_academique},
        {"$set": promo_doc},
        upsert=True
    )

    return promo_doc


async def supprimer_utilisateur_par_role_et_id(role: str, user_id: str):
    """
    Supprime un utilisateur (apprenti, tuteur, etc.) à partir de son rôle et son ID.
    """
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB manquante")

    if role not in ROLES_VALIDES:
        raise HTTPException(status_code=400, detail=f"Rôle invalide : {role}")

    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    collection = database.db[f"users_{role}"]
    result = await collection.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Aucun utilisateur '{role}' trouvé avec cet ID")

    return {
        "message": f"✅ Utilisateur '{role}' supprimé avec succès",
        "deleted_id": user_id,
        "role": role
    }



async def modifier_utilisateur_par_role_et_id(role: str, user_id: str, updates: dict):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB manquante")

    if role not in ROLES_VALIDES:
        raise HTTPException(status_code=400, detail=f"Rôle invalide : {role}")

    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    collection = database.db[f"users_{role}"]

    # ✅ Corrigé ici
    update_dict = {k: v for k, v in updates.items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await collection.update_one(
        {"_id": object_id},
        {"$set": update_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé ou données identiques")

    return {
        "message": f"✅ Utilisateur '{role}' modifié avec succès",
        "updated_id": user_id,
        "role": role,
        "updates_applied": update_dict
    }