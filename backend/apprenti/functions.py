from fastapi import HTTPException
from bson import ObjectId
import common.db as database
from datetime import datetime

ROLES_VALIDES = ["apprenti", "tuteur", "coordinatrice", "responsable_cursus"]
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

        # ✅ Infos de base
        infos = {
            "_id": str(apprenti["_id"]),
            "first_name": apprenti.get("first_name"),
            "last_name": apprenti.get("last_name"),
            "email": apprenti.get("email"),
            "phone": apprenti.get("phone"),
        }

        # 🔁 Ajout dynamique des rôles liés
        for role in ROLES_VALIDES:
            infos[role] = apprenti.get(role, None)

        return {
            "message": "✅ Données récupérées avec succès",
            "data": infos
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")
    


async def creer_entretien(data):
    apprenti_collection = get_collection("apprenti")
    tuteur_collection = get_collection("tuteur_pedagogique")
    maitre_collection = get_collection("maitre_apprentissage")
    jury_collection = get_collection("jury")

    # 🔍 1. Récupère l’apprenti
    apprenti = await apprenti_collection.find_one({"_id": ObjectId(data.apprenti_id)})
    if not apprenti:
        raise HTTPException(status_code=404, detail="Apprenti introuvable")

    # 🔍 2. Vérifie qu'il a un tuteur et un maître associés
    tuteur = apprenti.get("tuteur")
    maitre = apprenti.get("maitre")
    jury = apprenti.get("jury")

    if not tuteur or not maitre:
        raise HTTPException(status_code=400, detail="Tuteur ou Maître non associé à l’apprenti")

    # 📦 3. Création de l’objet entretien
    entretien = {
        "entretien_id": str(ObjectId()),
        "apprenti_id": str(apprenti["_id"]),
        "apprenti_nom": f"{apprenti.get('first_name')} {apprenti.get('last_name')}",
        "date": data.date.isoformat(),
        "sujet": data.sujet,
        "created_at": datetime.utcnow().isoformat(),
        "tuteur": tuteur,
        "maitre": maitre
    }
    if jury:
        entretien["jury"] = jury

    # 💾 4. Ajout dans chaque collection
    await apprenti_collection.update_one(
        {"_id": ObjectId(data.apprenti_id)},
        {"$push": {"entretiens": entretien}}
    )

    await tuteur_collection.update_one(
        {"_id": ObjectId(tuteur["tuteur_id"])},
        {"$push": {"entretiens": entretien}}
    )

    await maitre_collection.update_one(
        {"_id": ObjectId(maitre["maitre_id"])},
        {"$push": {"entretiens": entretien}}
    )

    if jury and "jury_id" in jury:
        await jury_collection.update_one(
            {"_id": ObjectId(jury["jury_id"])},
            {"$push": {"entretiens": entretien}}
        )

    return {
        "message": "✅ Entretien planifié avec succès",
        "entretien": entretien
    }


async def supprimer_entretien(apprenti_id: str, entretien_id: str):
    try:
        apprenti_collection = get_collection("apprenti")
        tuteur_collection = get_collection("tuteur_pedagogique")
        maitre_collection = get_collection("maitre_apprentissage")
        jury_collection = get_collection("jury")

        # 1️⃣ Récupérer l'apprenti
        apprenti = await apprenti_collection.find_one({"_id": ObjectId(apprenti_id)})
        if not apprenti:
            raise HTTPException(status_code=404, detail="Apprenti non trouvé")

        # 2️⃣ Supprimer l'entretien dans la collection apprenti
        result_apprenti = await apprenti_collection.update_one(
            {"_id": ObjectId(apprenti_id)},
            {"$pull": {"entretiens": {"entretien_id": entretien_id}}}
        )

        # 3️⃣ Supprimer aussi dans le tuteur (si défini)
        tuteur_info = apprenti.get("tuteur", {})
        if tuteur_info and "tuteur_id" in tuteur_info:
            await tuteur_collection.update_one(
                {"_id": ObjectId(tuteur_info["tuteur_id"])},
                {"$pull": {"entretiens": {"entretien_id": entretien_id}}}
            )

        # 4️⃣ Supprimer aussi dans le maître (si défini)
        maitre_info = apprenti.get("maitre", {})
        if maitre_info and "maitre_id" in maitre_info:
            await maitre_collection.update_one(
                {"_id": ObjectId(maitre_info["maitre_id"])},
                {"$pull": {"entretiens": {"entretien_id": entretien_id}}}
            )

        # 4️⃣ bis Supprimer aussi dans le jury (si défini)
        jury_info = apprenti.get("jury", {})
        if jury_info and "jury_id" in jury_info:
            await jury_collection.update_one(
                {"_id": ObjectId(jury_info["jury_id"])},
                {"$pull": {"entretiens": {"entretien_id": entretien_id}}}
            )

        # 5️⃣ Vérification finale
        if result_apprenti.modified_count == 0:
            raise HTTPException(status_code=404, detail="Entretien non trouvé ou déjà supprimé chez l'apprenti")

        return {
            "message": "🗑️ Entretien supprimé chez l'apprenti, le tuteur, le maître et le jury",
            "entretien_id": entretien_id,
            "apprenti_id": apprenti_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")