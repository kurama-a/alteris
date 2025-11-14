from fastapi import APIRouter, HTTPException,Body
from pydantic import BaseModel
from bson import ObjectId
import common.db as database
from models import AssocierTuteurRequest,UserUpdateModel
from models import AssocierResponsableCursusRequest,AssocierResponsablePromoRequest, AssocierMaitreRequest
from functions import (
    get_apprentis_by_annee_academique,
    supprimer_utilisateur_par_role_et_id,
    modifier_utilisateur_par_role_et_id,
    list_all_apprentis,
)
def get_collection_name_by_role(role: str) -> str:
    return f"users_{role.lower().replace(' ', '_')}"

def get_collection_from_role(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    return database.db[get_collection_name_by_role(role)]

admin_api = APIRouter(tags=["Admin"])


@admin_api.get("/apprentis", summary="Lister tous les apprentis pour l'administration")
async def get_all_apprentis():
    return await list_all_apprentis()

# ✅ Route POST /associer-tuteur
@admin_api.post("/associer-tuteur")
async def associer_tuteur(data: AssocierTuteurRequest):
    try:
        apprenti_collection = get_collection_from_role("apprenti")
        tuteur_collection = get_collection_from_role("tuteur_pedagogique")

        # 1️⃣ Vérifie que le tuteur existe
        tuteur = await tuteur_collection.find_one({"_id": ObjectId(data.tuteur_id)})
        if not tuteur:
            raise HTTPException(status_code=404, detail="Tuteur inexistant")

        # 2️⃣ Construit les infos à enregistrer
        tuteur_info = {
            "tuteur_id": str(tuteur["_id"]),
            "first_name": tuteur.get("first_name"),
            "last_name": tuteur.get("last_name"),
            "email": tuteur.get("email"),
            "phone": tuteur.get("phone"),
        }

        # 3️⃣ Met à jour l'apprenti avec les infos du tuteur
        result = await apprenti_collection.update_one(
            {"_id": ObjectId(data.apprenti_id)},
            {"$set": {"tuteur": tuteur_info}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

        return {
            "message": "✅ Tuteur associé avec succès",
            "apprenti_id": data.apprenti_id,
            "tuteur": tuteur_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")
    


@admin_api.get("/promos/generate/annee/{annee_academique}")
async def generate_promo_by_annee(annee_academique: str):
    """
    Génère une promo à partir de l'année académique (ex: 'E5a', '2024-2025', etc.)
    """
    promo = await get_apprentis_by_annee_academique(annee_academique)
    return {
        "message": f"✅ Promo '{annee_academique}' générée avec succès",
        "data": promo
    }

@admin_api.post("/associer-maitre")
async def associer_maitre(data: AssocierMaitreRequest):
    apprenti_collection = get_collection_from_role("apprenti")
    maitre_collection = get_collection_from_role("maitre_apprentissage")

    maitre = await maitre_collection.find_one({"_id": ObjectId(data.maitre_id)})
    if not maitre:
        raise HTTPException(status_code=404, detail="Maître d’apprentissage inexistant")

    maitre_info = {
        "maitre_id": str(maitre["_id"]),
        "first_name": maitre.get("first_name"),
        "last_name": maitre.get("last_name"),
        "email": maitre.get("email"),
        "phone": maitre.get("phone"),
    }

    result = await apprenti_collection.update_one(
        {"_id": ObjectId(data.apprenti_id)},
        {"$set": {"maitre": maitre_info}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

    return {
        "message": "✅ Maître d’apprentissage associé avec succès",
        "apprenti_id": data.apprenti_id,
        "maitre": maitre_info
    }

@admin_api.post("/associer-responsable-cursus")
async def associer_responsable_cursus(data: AssocierResponsablePromoRequest):
    db = database.db
    if db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    # 🔍 Récupération des collections
    promo_collection = db["promos"]
    responsable_collection = db["users_responsable_cursus"]

    # 🔍 Étape 1 : Vérifier que le responsable existe
    responsable = await responsable_collection.find_one({"_id": ObjectId(data.responsable_id)})
    if not responsable:
        raise HTTPException(status_code=404, detail="Responsable de cursus introuvable")

    responsable_info = {
        "responsable_id": str(responsable["_id"]),
        "first_name": responsable.get("first_name"),
        "last_name": responsable.get("last_name"),
        "email": responsable.get("email"),
        "phone": responsable.get("phone"),
    }

    # 🔄 Étape 2 : Associer au document promo via update
    result = await promo_collection.update_one(
        {"annee_academique": data.promo_annee_academique},
        {"$set": {"responsable_cursus": responsable_info}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Promotion non trouvée ou déjà associée")

    return {
        "message": "✅ Responsable de cursus associé avec succès",
        "promo": data.promo_annee_academique,
        "responsable": responsable_info
    }

@admin_api.post("/associer-responsable_cursus-apprenti")
async def associer_responsable_cursus(data: AssocierResponsableCursusRequest):
    apprenti_collection = get_collection_from_role("apprenti")
    responsable_cursus_collection = get_collection_from_role("responsable_cursus")

    responsable_cursus = await responsable_cursus_collection.find_one({"_id": ObjectId(data.responsable_cursus_id)})
    if not responsable_cursus:
        raise HTTPException(status_code=404, detail="responsable_cursus inexistant")

    responsable_cursus_info = {
        "responsable_cursus_id": str(responsable_cursus["_id"]),
        "first_name": responsable_cursus.get("first_name"),
        "last_name": responsable_cursus.get("last_name"),
        "email": responsable_cursus.get("email"),
        "phone": responsable_cursus.get("phone"),
    }

    result = await apprenti_collection.update_one(
        {"_id": ObjectId(data.apprenti_id)},
        {"$set": {"responsable_cursus": responsable_cursus_info}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

    return {
        "message": "✅ responsable_cursus associé avec succès",
        "apprenti_id": data.apprenti_id,
        "responsable_cursus": responsable_cursus_info
    }


@admin_api.delete("/user/{role}/{user_id}", summary="Supprimer un utilisateur par rôle et ID")
async def delete_user(role: str, user_id: str):
    """
    Supprime un utilisateur d'une collection spécifique (ex: users_apprenti) à partir de son rôle et ID.

    Exemple :
    - DELETE /admin/user/apprenti/65ab1234...
    - DELETE /admin/user/maitre_apprentissage/65ab5678...
    """
    return await supprimer_utilisateur_par_role_et_id(role, user_id)

@admin_api.put("/user/{role}/{user_id}", summary="Modifier un utilisateur par rôle et ID")
async def update_user(role: str, user_id: str, payload: dict = Body(...)):
    """
    Modifie un utilisateur dans une collection spécifique (users_<role>) à partir de son ID.

    Exemple :
    - PUT /admin/user/apprenti/65ab1234...
      Body: { "first_name": "Ali", "phone": "0601020304" }
    """
    return await modifier_utilisateur_par_role_et_id(role, user_id, payload)


@admin_api.put("/user/{role}/{user_id}", summary="Modifier un utilisateur (apprenti, tuteur, etc.)")
async def update_user(role: str, user_id: str, payload: dict):
    return await modifier_utilisateur_par_role_et_id(role, user_id, payload)
