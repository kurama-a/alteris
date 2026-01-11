from fastapi import HTTPException
from datetime import datetime
from uuid import uuid4
from typing import List, Optional
import common.db as database
from bson import ObjectId
from admin.models import UserUpdateModel, PromotionUpsertRequest, PromotionSemesterPayload

ROLES_VALIDES = [
    "apprenti",
    "tuteur_pedagogique",
    "maitre_apprentissage",
    "coordinatrice",
    "responsable_cursus",
    "entreprise",
    "jury",
    "professeur",
    "intervenant",
    "admin",
    "ecole",
]

ROLE_REFERENCES = {
    "tuteur_pedagogique": {
        "apprenti_field": "tuteur",
        "id_field": "tuteur_id",
        "entretien_field": "tuteur",
    },
    "maitre_apprentissage": {
        "apprenti_field": "maitre",
        "id_field": "maitre_id",
        "entretien_field": "maitre",
    },
    "coordinatrice": {
        "apprenti_field": "coordinatrice",
        "id_field": "coordinatrice_id",
    },
    "responsable_cursus": {
        "apprenti_field": "responsable_cursus",
        "id_field": "responsable_cursus_id",
    },
    "entreprise": {
        "apprenti_field": "company",
        "id_field": "entreprise_id",
    },
}


def _snake_to_camel_case(key: str) -> str:
    parts = key.split("_")
    if not parts:
        return key
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def _extract_semester_value(raw: dict, key: str):
    if not isinstance(raw, dict):
        return None
    candidates = [key]
    camel_key = _snake_to_camel_case(key)
    compact_key = key.replace("_", "")
    if camel_key not in candidates:
        candidates.append(camel_key)
    if compact_key not in candidates:
        candidates.append(compact_key)
    for candidate in candidates:
        value = raw.get(candidate)
        if value not in (None, ""):
            return value
    return None


def _serialize_semesters(raw_semesters):
    serialized = []
    if not raw_semesters:
        return serialized
    for raw in sorted(raw_semesters, key=lambda entry: entry.get("order", 0)):
        name = raw.get("name")
        if not name:
            continue
        deliverables = []
        for deliverable in sorted(raw.get("deliverables", []), key=lambda entry: entry.get("order", 0)):
            deliverables.append({
                "deliverable_id": deliverable.get("deliverable_id") or deliverable.get("id"),
                "title": deliverable.get("title"),
                "description": deliverable.get("description"),
                "due_date": deliverable.get("due_date"),
                "order": deliverable.get("order", 0),
            })
        serialized.append({
            "semester_id": raw.get("semester_id") or raw.get("id"),
            "name": name,
            "start_date": _extract_semester_value(raw, "start_date"),
            "end_date": _extract_semester_value(raw, "end_date"),
            "order": raw.get("order", 0),
            "deliverables": deliverables,
        })
    return serialized


def _build_semesters_update(semesters: Optional[List[PromotionSemesterPayload]]):
    if semesters is None:
        return None

    normalized: List[dict] = []
    for index, semester in enumerate(semesters):
        name = semester.name.strip()
        if not name:
            continue
        normalized_semester = {
            "semester_id": semester.semester_id or str(uuid4()),
            "name": name,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "order": semester.order if semester.order is not None else index,
            "deliverables": [],
        }
        for deliverable_index, deliverable in enumerate(semester.deliverables):
            title = deliverable.title.strip()
            if not title:
                continue
            normalized_semester["deliverables"].append({
                "deliverable_id": deliverable.deliverable_id or str(uuid4()),
                "title": title,
                "due_date": deliverable.due_date,
                "description": deliverable.description,
                "order": deliverable.order if deliverable.order is not None else deliverable_index,
            })
        normalized.append(normalized_semester)
    return normalized


def _serialize_promotion_document(document: dict) -> dict:
    return {
        "id": str(document.get("_id", "")),
        "annee_academique": document.get("annee_academique"),
        "label": document.get("label"),
        "apprentis": document.get("apprentis"),
        "nb_apprentis": document.get("nb_apprentis", 0),
        "coordinators": document.get("coordinators", []),
        "next_milestone": document.get("next_milestone"),
        "responsable_cursus": document.get("responsable_cursus"),
        "semesters": _serialize_semesters(document.get("semesters", [])),
        "updated_at": document.get("updated_at"),
        "created_at": document.get("created_at"),
    }

async def get_apprentis_by_annee_academique(annee_academique: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection_apprenti = database.db["users_apprenti"]
    collection_promo = database.db["promos"]

    apprentis_meme_promo = await collection_apprenti.find(
        {"annee_academique": annee_academique}
    ).to_list(length=None)

    if not apprentis_meme_promo:
        raise HTTPException(status_code=404, detail="Aucun apprenti trouvé pour cette année académique")

    promo_base_fields = {
        "annee_academique": annee_academique,
        "apprentis": apprentis_meme_promo,
        "nb_apprentis": len(apprentis_meme_promo),
        "apprentis": [{
            "_id": str(apprenti["_id"]),
            "first_name": apprenti.get("first_name"),
            "last_name": apprenti.get("last_name"),
            "email": apprenti.get("email"),
            "phone": apprenti.get("phone")
        } for apprenti in apprentis_meme_promo],
        "updated_at": datetime.utcnow(),
    }

    await collection_promo.update_one(
        {"annee_academique": annee_academique},
        {
            "$set": promo_base_fields,
            "$setOnInsert": {
                "label": f"Promotion {annee_academique}",
                "coordinators": [],
                "next_milestone": None,
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True
    )

    updated = await collection_promo.find_one({"annee_academique": annee_academique})
    if not updated:
        raise HTTPException(status_code=500, detail="Impossible de générer la promotion demandée")
    return _serialize_promotion_document(updated)


async def _sync_promotion_apprentices_if_available(annee_academique: str):
    """
    Tentative de synchronisation des apprentis d'une promotion si l'année est déjà utilisée.
    Ne bloque pas la création si aucun apprenti n'est encore associé.
    """
    try:
        await get_apprentis_by_annee_academique(annee_academique)
    except HTTPException as exc:
        if exc.status_code not in (400, 404):
            raise

async def list_all_apprentis():
    """
    Retourne l'ensemble des apprentis avec les informations utiles pour la sélection côté admin.
    """
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection_apprenti = database.db["users_apprenti"]
    apprentis = []
    cursor = collection_apprenti.find()
    async for apprenti in cursor:
        first_name = apprenti.get("first_name") or ""
        last_name = apprenti.get("last_name") or ""
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = apprenti.get("fullName") or apprenti.get("name") or apprenti.get("email", "")
        apprentis.append({
            "id": str(apprenti.get("_id") or ""),
            "fullName": full_name,
            "email": apprenti.get("email", "")
        })

    return {"apprentis": apprentis}


async def supprimer_utilisateur_par_role_et_id(role: str, user_id: str):
    """
    Supprime un utilisateur (apprenti, tuteur, etc.) à partir de son rôle et son ID.
    Nettoie aussi les références associées dans d'autres collections (ex : apprentis).
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

    # 🔄 Nettoyage dans les apprentis où ce profil était référencé
    apprenti_collection = database.db["users_apprenti"]

    if role == "tuteur_pedagogique":
        await apprenti_collection.update_many(
            {"tuteur.tuteur_id": str(object_id)},
            {"$unset": {"tuteur": ""}}
        )

    elif role == "coordinatrice":
        await apprenti_collection.update_many(
            {"coordinatrice.coordinatrice_id": str(object_id)},
            {"$unset": {"coordinatrice": ""}}
        )

    elif role == "responsable_cursus":
        await apprenti_collection.update_many(
            {"responsable_cursus.responsable_cursus_id": str(object_id)},
            {"$unset": {"responsable_cursus": ""}}
        )
    elif role == "entreprise":
        await apprenti_collection.update_many(
            {"company.entreprise_id": str(object_id)},
            {"$unset": {"company": ""}}
        )

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
    update_dict = {k: v for k, v in updates.items() if v is not None}

    if not update_dict:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    result = await collection.update_one(
        {"_id": object_id},
        {"$set": update_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé ou données identiques")

    updated_document = await collection.find_one({"_id": object_id})

    reference_config = ROLE_REFERENCES.get(role)
    if reference_config and updated_document:
        apprenti_collection = database.db["users_apprenti"]
        apprenti_field = reference_config["apprenti_field"]
        id_field = reference_config["id_field"]
        if role == "entreprise":
            reference_data = {
                id_field: str(object_id),
                "name": updated_document.get("raisonSociale") or updated_document.get("email") or "Entreprise partenaire",
                "address": updated_document.get("adresse") or "Adresse non renseign�e",
                "dates": updated_document.get("dates") or "P�riode non renseign�e",
                "siret": updated_document.get("siret"),
                "email": updated_document.get("email"),
            }
        else:
            reference_data = {
                id_field: str(object_id),
                "first_name": updated_document.get("first_name"),
                "last_name": updated_document.get("last_name"),
                "email": updated_document.get("email"),
                "phone": updated_document.get("phone"),
            }

        await apprenti_collection.update_many(
            {f"{apprenti_field}.{id_field}": str(object_id)},
            {"$set": {apprenti_field: reference_data}}
        )

        entretien_field = reference_config.get("entretien_field")
        if entretien_field:
            await apprenti_collection.update_many(
                {f"entretiens.{entretien_field}.{id_field}": str(object_id)},
                {
                    "$set": {
                        f"entretiens.$[entretien].{entretien_field}": reference_data
                    }
                },
                array_filters=[
                    {f"entretien.{entretien_field}.{id_field}": str(object_id)}
                ],
            )

    return {
        "message": f"✅ Utilisateur '{role}' modifié avec succès",
        "updated_id": user_id,
        "role": role,
        "updates_applied": update_dict
    }


async def list_promotions():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection_promo = database.db["promos"]
    cursor = collection_promo.find().sort("annee_academique", 1)
    promotions = []
    async for promo in cursor:
        promotions.append(_serialize_promotion_document(promo))
    return {"promotions": promotions}


async def create_or_update_promotion(payload: PromotionUpsertRequest):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection_promo = database.db["promos"]
    await _sync_promotion_apprentices_if_available(payload.annee_academique)

    updates = {
        "label": payload.label or f"Promotion {payload.annee_academique}",
        "coordinators": payload.coordinators,
        "next_milestone": payload.next_milestone,
        "updated_at": datetime.utcnow(),
    }

    semesters_payload = _build_semesters_update(payload.semesters)
    if semesters_payload is not None:
        updates["semesters"] = semesters_payload

    if payload.responsable_id:
        responsable_collection = database.db["users_responsable_cursus"]
        try:
            responsable = await responsable_collection.find_one({"_id": ObjectId(payload.responsable_id)})
        except Exception:
            responsable = None
        if not responsable:
            raise HTTPException(status_code=404, detail="Responsable de cursus introuvable")
        updates["responsable_cursus"] = {
            "responsable_cursus_id": str(responsable["_id"]),
            "first_name": responsable.get("first_name"),
            "last_name": responsable.get("last_name"),
            "email": responsable.get("email"),
            "phone": responsable.get("phone"),
        }

    await collection_promo.update_one(
        {"annee_academique": payload.annee_academique},
        {"$set": updates},
        upsert=True
    )

    promo = await collection_promo.find_one({"annee_academique": payload.annee_academique})
    if not promo:
        raise HTTPException(status_code=500, detail="Impossible de mettre à jour la promotion")
    return _serialize_promotion_document(promo)


async def update_promotion_timeline(annee_academique: str, semesters: List[PromotionSemesterPayload]):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection_promo = database.db["promos"]
    normalized_semesters = _build_semesters_update(semesters) or []
    result = await collection_promo.update_one(
        {"annee_academique": annee_academique},
        {
            "$set": {
                "semesters": normalized_semesters,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=False,
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promotion introuvable")

    promo = await collection_promo.find_one({"annee_academique": annee_academique})
    if not promo:
        raise HTTPException(status_code=500, detail="Impossible de charger la promotion mise a jour")
    return _serialize_promotion_document(promo)


async def list_responsables_cursus():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")

    collection = database.db["users_responsable_cursus"]
    responsables = []
    cursor = collection.find().sort("last_name", 1)
    async for responsable in cursor:
        first_name = responsable.get("first_name") or ""
        last_name = responsable.get("last_name") or ""
        full_name = f"{first_name} {last_name}".strip() or responsable.get("email", "")
        responsables.append({
            "id": str(responsable.get("_id") or ""),
            "fullName": full_name,
            "email": responsable.get("email", ""),
        })
    return {"responsables": responsables}
