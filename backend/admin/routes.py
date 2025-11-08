from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
import common.db as database
from models import (
    AssocierTuteurRequest,
    AssocierMaitreRequest,
    AssocierResponsableRequest,
    AssocierEntreprisesRequest,
    AssocierEcoleRequest,
    AssocierCoordinatriceRequest
)
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
    

@admin_api.post("/associer-maitre")
async def associer_maitre(data: AssocierMaitreRequest):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")

@admin_api.post("/associer-coordonatrice")
async def associer_coordonatrice(data: AssocierCoordinatriceRequest):
    try:
        apprenti_collection = get_collection_from_role("apprenti")
        coordo_collection = get_collection_from_role("coordinatrice")

        coordo = await coordo_collection.find_one({"_id": ObjectId(data.coordinatrice_id)})
        if not coordo:
            raise HTTPException(status_code=404, detail="Coordonnatrice inexistante")

        coordo_info = {
            "coordonatrice_id": str(coordo["_id"]),
            "first_name": coordo.get("first_name"),
            "last_name": coordo.get("last_name"),
            "email": coordo.get("email"),
            "phone": coordo.get("phone"),
        }

        result = await apprenti_collection.update_one(
            {"_id": ObjectId(data.apprenti_id)},
            {"$set": {"coordonatrice": coordo_info}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

        return {
            "message": "✅ Coordonnatrice associée avec succès",
            "apprenti_id": data.apprenti_id,
            "coordonatrice": coordo_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")

@admin_api.post("/associer-responsable")
async def associer_responsable(data: AssocierResponsableRequest):
    try:
        apprenti_collection = get_collection_from_role("apprenti")
        resp_collection = get_collection_from_role("responsable_cursus")

        resp = await resp_collection.find_one({"_id": ObjectId(data.responsable_id)})
        if not resp:
            raise HTTPException(status_code=404, detail="Responsable de formation inexistant")

        resp_info = {
            "responsable_id": str(resp["_id"]),
            "first_name": resp.get("first_name"),
            "last_name": resp.get("last_name"),
            "email": resp.get("email"),
            "phone": resp.get("phone"),
        }

        result = await apprenti_collection.update_one(
            {"_id": ObjectId(data.apprenti_id)},
            {"$set": {"responsable": resp_info}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

        return {
            "message": "✅ Responsable de formation associé avec succès",
            "apprenti_id": data.apprenti_id,
            "responsable": resp_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")

@admin_api.post("/associer-entreprise")
async def associer_entreprise(data: AssocierEntreprisesRequest):
    try:
        apprenti_collection = get_collection_from_role("apprenti")
        ent_collection = get_collection_from_role("entreprise_externe")

        ent = await ent_collection.find_one({"_id": ObjectId(data.entreprise_id)})
        if not ent:
            raise HTTPException(status_code=404, detail="Entreprise externe inexistante")

        ent_info = {
            "entreprise_id": str(ent["_id"]),
            "raisonSociale": ent.get("raisonSociale"),
            "siret": ent.get("siret"),
            "email": ent.get("email"),
            "adresse": ent.get("adresse"),
        }

        result = await apprenti_collection.update_one(
            {"_id": ObjectId(data.apprenti_id)},
            {"$set": {"entreprise": ent_info}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

        return {
            "message": "✅ Entreprise externe associée avec succès",
            "apprenti_id": data.apprenti_id,
            "entreprise": ent_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")

@admin_api.post("/associer-ecole")
async def associer_ecole(data: AssocierEcoleRequest):
    try:
        apprenti_collection = get_collection_from_role("apprenti")
        ecole_collection = get_collection_from_role("ecole")

        ecole = await ecole_collection.find_one({"_id": ObjectId(data.ecole_id)})
        if not ecole:
            raise HTTPException(status_code=404, detail="École inexistante")

        ecole_info = {
            "ecole_id": str(ecole["_id"]),
            "raisonSociale": ecole.get("raisonSociale"),
            "email": ecole.get("email"),
            "adresse": ecole.get("adresse"),
        }

        result = await apprenti_collection.update_one(
            {"_id": ObjectId(data.apprenti_id)},
            {"$set": {"ecole": ecole_info}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Apprenti non trouvé ou déjà associé")

        return {
            "message": "✅ École associée avec succès",
            "apprenti_id": data.apprenti_id,
            "ecole": ecole_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")