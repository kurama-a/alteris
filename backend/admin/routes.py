from fastapi import APIRouter, HTTPException,Body
from pydantic import BaseModel
from bson import ObjectId
import common.db as database
from models import (
    AssocierTuteurRequest,
    UserUpdateModel,
    AssocierResponsableCursusRequest,
    AssocierResponsablePromoRequest,
    AssocierMaitreRequest,
    AssocierEcoleRequest,
    AssocierEntrepriseRequest,
)
from functions import get_apprentis_by_annee_academique ,supprimer_utilisateur_par_role_et_id,modifier_utilisateur_par_role_et_id
def get_collection_name_by_role(role: str) -> str:
    return f"users_{role.lower().replace(' ', '_')}"

def get_collection_from_role(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisée")
    return database.db[get_collection_name_by_role(role)]

admin_api = APIRouter(tags=["Admin"])

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

        # 1️⃣ bis: Vérifie que l'apprenti existe
        apprenti = await apprenti_collection.find_one({"_id": ObjectId(data.apprenti_id)})
        if not apprenti:
            raise HTTPException(status_code=404, detail="Apprenti inexistant")

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

        # 4️⃣ Ajoute aussi les infos de l'apprenti dans le tuteur (liste 'apprentis')
        apprenti_info = {
            "apprenti_id": str(apprenti["_id"]),
            "first_name": apprenti.get("first_name"),
            "last_name": apprenti.get("last_name"),
            "email": apprenti.get("email"),
            "phone": apprenti.get("phone"),
            "annee_academique": apprenti.get("annee_academique"),
        }

        # Assure l'idempotence: retire l'entrée si elle existe puis ajoute la version à jour
        await tuteur_collection.update_one(
            {"_id": ObjectId(data.tuteur_id)},
            {"$pull": {"apprentis": {"apprenti_id": str(apprenti["_id"])}}}
        )
        await tuteur_collection.update_one(
            {"_id": ObjectId(data.tuteur_id)},
            {"$addToSet": {"apprentis": apprenti_info}}
        )

        return {
            "message": "✅ Tuteur associé avec succès (bidirectionnel)",
            "apprenti_id": data.apprenti_id,
            "tuteur": tuteur_info,
            "apprenti_ajoute_au_tuteur": apprenti_info,
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

    # 🔍 Vérifie que le maître existe
    maitre = await maitre_collection.find_one({"_id": ObjectId(data.maitre_id)})
    if not maitre:
        raise HTTPException(status_code=404, detail="Maître d’apprentissage inexistant")

    # 🔍 Vérifie que l'apprenti existe
    apprenti = await apprenti_collection.find_one({"_id": ObjectId(data.apprenti_id)})
    if not apprenti:
        raise HTTPException(status_code=404, detail="Apprenti inexistant")

    # 📦 Construction des infos à associer
    maitre_info = {
        "maitre_id": str(maitre["_id"]),
        "first_name": maitre.get("first_name"),
        "last_name": maitre.get("last_name"),
        "email": maitre.get("email"),
        "phone": maitre.get("phone"),
    }

    # 🔁 Mise à jour de l’apprenti
    result = await apprenti_collection.update_one(
        {"_id": ObjectId(data.apprenti_id)},
        {"$set": {"maitre": maitre_info}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

    # 🔁 Ajoute aussi les infos de l'apprenti dans le maître (liste 'apprentis')
    apprenti_info = {
        "apprenti_id": str(apprenti["_id"]),
        "first_name": apprenti.get("first_name"),
        "last_name": apprenti.get("last_name"),
        "email": apprenti.get("email"),
        "phone": apprenti.get("phone"),
        "annee_academique": apprenti.get("annee_academique"),
    }
    await maitre_collection.update_one(
        {"_id": ObjectId(data.maitre_id)},
        {"$pull": {"apprentis": {"apprenti_id": str(apprenti["_id"])}}}
    )
    await maitre_collection.update_one(
        {"_id": ObjectId(data.maitre_id)},
        {"$addToSet": {"apprentis": apprenti_info}}
    )

    return {
        "message": "✅ Maître d’apprentissage associé avec succès (bidirectionnel)",
        "apprenti_id": data.apprenti_id,
        "maitre": maitre_info,
        "apprenti_ajoute_au_maitre": apprenti_info,
    }

# ✅ Associer une ÉCOLE à un apprenti (et inversement)
@admin_api.post("/associer-ecole")
async def associer_ecole(data: AssocierEcoleRequest):
    db = database.db
    if db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    apprenti_collection = get_collection_from_role("apprenti")
    ecole_collection = get_collection_from_role("ecole")

    # Vérifications d'existence
    apprenti = await apprenti_collection.find_one({"_id": ObjectId(data.apprenti_id)})
    if not apprenti:
        raise HTTPException(status_code=404, detail="Apprenti inexistant")

    ecole = await ecole_collection.find_one({"_id": ObjectId(data.ecole_id)})
    if not ecole:
        raise HTTPException(status_code=404, detail="École inexistante")

    # Infos structurées
    ecole_info = {
        "ecole_id": str(ecole["_id"]),
        "raisonSociale": ecole.get("raisonSociale"),
        "siret": ecole.get("siret"),
        "email": ecole.get("email"),
        "adresse": ecole.get("adresse"),
    }
    apprenti_info = {
        "apprenti_id": str(apprenti["_id"]),
        "first_name": apprenti.get("first_name"),
        "last_name": apprenti.get("last_name"),
        "email": apprenti.get("email"),
        "phone": apprenti.get("phone"),
        "annee_academique": apprenti.get("annee_academique"),
    }

    # Mise à jour côté apprenti
    res_apprenti = await apprenti_collection.update_one(
        {"_id": ObjectId(data.apprenti_id)},
        {"$set": {"ecole": ecole_info}}
    )
    if res_apprenti.matched_count == 0:
        raise HTTPException(status_code=404, detail="Apprenti non trouvé")

    # Mise à jour côté école (liste des apprentis)
    await ecole_collection.update_one(
        {"_id": ObjectId(data.ecole_id)},
        {"$pull": {"apprentis": {"apprenti_id": str(apprenti["_id"])}}}
    )
    await ecole_collection.update_one(
        {"_id": ObjectId(data.ecole_id)},
        {"$addToSet": {"apprentis": apprenti_info}}
    )

    return {
        "message": "✅ École associée avec succès (bidirectionnel)",
        "apprenti_id": data.apprenti_id,
        "ecole": ecole_info,
        "apprenti_ajoute_a_ecole": apprenti_info,
    }

# ✅ Associer une ENTREPRISE à un apprenti (et inversement)
@admin_api.post("/associer-entreprise_externe")
async def associer_entreprise(data: AssocierEntrepriseRequest):
    db = database.db
    if db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    apprenti_collection = get_collection_from_role("apprenti")
    entreprise_collection = get_collection_from_role("entreprise_externe")

    # Vérifications d'existence
    apprenti = await apprenti_collection.find_one({"_id": ObjectId(data.apprenti_id)})
    if not apprenti:
        raise HTTPException(status_code=404, detail="Apprenti inexistant")

    entreprise = await entreprise_collection.find_one({"_id": ObjectId(data.entreprise_id)})
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise inexistante")

    # Infos structurées
    entreprise_info = {
        "entreprise_id": str(entreprise["_id"]),
        "raisonSociale": entreprise.get("raisonSociale"),
        "siret": entreprise.get("siret"),
        "email": entreprise.get("email"),
        "adresse": entreprise.get("adresse"),
    }
    apprenti_info = {
        "apprenti_id": str(apprenti["_id"]),
        "first_name": apprenti.get("first_name"),
        "last_name": apprenti.get("last_name"),
        "email": apprenti.get("email"),
        "phone": apprenti.get("phone"),
        "annee_academique": apprenti.get("annee_academique"),
    }

    # Mise à jour côté apprenti
    res_apprenti = await apprenti_collection.update_one(
        {"_id": ObjectId(data.apprenti_id)},
        {"$set": {"entreprise_externe": entreprise_info}}
    )
    if res_apprenti.matched_count == 0:
        raise HTTPException(status_code=404, detail="Apprenti non trouvé")

    # Mise à jour côté entreprise (liste des apprentis)
    await entreprise_collection.update_one(
        {"_id": ObjectId(data.entreprise_id)},
        {"$pull": {"apprentis": {"apprenti_id": str(apprenti["_id"])}}}
    )
    await entreprise_collection.update_one(
        {"_id": ObjectId(data.entreprise_id)},
        {"$addToSet": {"apprentis": apprenti_info}}
    )

    return {
        "message": "✅ Entreprise externe associée avec succès (bidirectionnel)",
        "apprenti_id": data.apprenti_id,
        "entreprise_externe": entreprise_info,
        "apprenti_ajoute_a_entreprise_externe": apprenti_info,
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