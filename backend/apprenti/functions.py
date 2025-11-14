from fastapi import HTTPException
from bson import ObjectId
from typing import Any, Dict, Optional
from urllib.parse import quote_plus
import common.db as database
from datetime import datetime

ROLES_VALIDES = [
    "apprenti",
    "tuteur",
    "tuteur_pedagogique",
    "maitre",
    "coordinatrice",
    "responsable_cursus",
]
DEFAULT_JOURNAL_HERO = (
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?q=80&w=2400&auto=format&fit=crop"
)


def get_collection(role: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[f"users_{role}"]


def _build_full_name(apprenti: Dict[str, Any]) -> str:
    first_name = (apprenti.get("first_name") or "").strip()
    last_name = (apprenti.get("last_name") or "").strip()
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = (
            apprenti.get("full_name")
            or apprenti.get("name")
            or apprenti.get("email")
            or "Apprenti"
        )
    return full_name


def _build_profile(apprenti: Dict[str, Any], full_name: str) -> Dict[str, Any]:
    profile = apprenti.get("profile") or {}
    avatar_url = profile.get("avatarUrl") or profile.get("avatar_url")
    if not avatar_url:
        avatar_seed = full_name or apprenti.get("email") or "alteris"
        avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={quote_plus(avatar_seed)}"
    return {
        "age": profile.get("age") or apprenti.get("age") or 0,
        "position": profile.get("position") or apprenti.get("position") or "Apprenti",
        "phone": profile.get("phone") or apprenti.get("phone") or "",
        "city": profile.get("city") or apprenti.get("city") or "",
        "avatarUrl": avatar_url,
    }


def _build_company(apprenti: Dict[str, Any]) -> Dict[str, Any]:
    company = apprenti.get("company") or {}
    return {
        "name": company.get("name") or apprenti.get("company_name") or "Entreprise partenaire",
        "dates": company.get("dates") or apprenti.get("company_dates") or "Periode non renseignee",
        "address": company.get("address")
        or apprenti.get("company_address")
        or apprenti.get("address")
        or "Adresse non renseignee",
    }


def _build_school(apprenti: Dict[str, Any]) -> Dict[str, Any]:
    school = apprenti.get("school") or {}
    return {
        "name": school.get("name") or apprenti.get("school_name") or "ESEO",
        "program": school.get("program") or apprenti.get("program") or "Programme non renseigne",
    }


def _format_contact(
    record: Optional[Dict[str, Any]], title: str, default_role: str
) -> Optional[Dict[str, Any]]:
    if not isinstance(record, dict):
        return None

    first = (record.get("first_name") or "").strip()
    last = (record.get("last_name") or "").strip()
    name = f"{first} {last}".strip() or record.get("name")
    if not name:
        return None

    return {
        "title": record.get("title") or title,
        "name": name,
        "role": record.get("role") or default_role,
        "email": record.get("email") or "",
        "phone": record.get("phone"),
    }


def _fallback_contact(title: str, role_label: str) -> Dict[str, Any]:
    return {
        "title": title,
        "name": "Contact a completer",
        "role": role_label,
        "email": "",
        "phone": None,
    }


def _build_tutors(apprenti: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    enterprise_primary = _format_contact(
        apprenti.get("maitre") or apprenti.get("maitre_apprentissage"),
        "Maitre d'apprentissage",
        "Referent entreprise",
    )
    enterprise_secondary = _format_contact(
        apprenti.get("tuteur") or apprenti.get("coordinatrice"),
        "Tuteur entreprise",
        "Tuteur secondaire",
    )
    pedagogic = _format_contact(
        apprenti.get("tuteur_pedagogique") or apprenti.get("responsable_cursus"),
        "Tuteur pedagogique",
        "Referent pedagogique",
    )

    contacts = [contact for contact in (enterprise_primary, enterprise_secondary, pedagogic) if contact]
    if not contacts:
        return None

    return {
        "enterprisePrimary": enterprise_primary
        or _fallback_contact("Maitre d'apprentissage", "Referent entreprise"),
        "enterpriseSecondary": enterprise_secondary
        or _fallback_contact("Tuteur entreprise", "Tuteur secondaire"),
        "pedagogic": pedagogic or _fallback_contact("Tuteur pedagogique", "Referent pedagogique"),
    }


def _build_journal_payload(apprenti: Dict[str, Any]) -> Dict[str, Any]:
    full_name = _build_full_name(apprenti)
    return {
        "id": str(apprenti.get("_id")),
        "email": apprenti.get("email", ""),
        "fullName": full_name,
        "profile": _build_profile(apprenti, full_name),
        "company": _build_company(apprenti),
        "school": _build_school(apprenti),
        "tutors": _build_tutors(apprenti),
        "journalHeroImageUrl": apprenti.get("journalHeroImageUrl")
        or apprenti.get("journal_hero_image_url")
        or DEFAULT_JOURNAL_HERO,
    }


async def recuperer_infos_apprenti_completes(apprenti_id: str):
    try:
        apprenti_collection = get_collection("apprenti")

        # ?? R�cup�ration de l'apprenti
        apprenti = await apprenti_collection.find_one({"_id": ObjectId(apprenti_id)})
        if not apprenti:
            raise HTTPException(status_code=404, detail="Apprenti introuvable")

        # ? Infos de base
        full_name = _build_full_name(apprenti)
        infos = {
            "_id": str(apprenti["_id"]),
            "first_name": apprenti.get("first_name"),
            "last_name": apprenti.get("last_name"),
            "email": apprenti.get("email"),
            "phone": apprenti.get("phone"),
            "full_name": full_name,
        }

        # ?? Ajout dynamique des r�les li�s
        for role in ROLES_VALIDES:
            infos[role] = apprenti.get(role, None)

        infos["journal"] = _build_journal_payload(apprenti)

        return {
            "message": "? Donn�es r�cup�r�es avec succ�s",
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

    # 🔍 1. Récupère l’apprenti
    apprenti = await apprenti_collection.find_one({"_id": ObjectId(data.apprenti_id)})
    if not apprenti:
        raise HTTPException(status_code=404, detail="Apprenti introuvable")

    # 🔍 2. Vérifie qu'il a un tuteur et un maître associés
    tuteur = apprenti.get("tuteur")
    maitre = apprenti.get("maitre")

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

    return {
        "message": "✅ Entretien planifié avec succès",
        "entretien": entretien
    }


async def supprimer_entretien(apprenti_id: str, entretien_id: str):
    try:
        apprenti_collection = get_collection("apprenti")
        tuteur_collection = get_collection("tuteur_pedagogique")
        maitre_collection = get_collection("maitre_apprentissage")

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

        # 5️⃣ Vérification finale
        if result_apprenti.modified_count == 0:
            raise HTTPException(status_code=404, detail="Entretien non trouvé ou déjà supprimé chez l'apprenti")

        return {
            "message": "🗑️ Entretien supprimé chez l'apprenti, le tuteur et le maître",
            "entretien_id": entretien_id,
            "apprenti_id": apprenti_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")
