from fastapi import HTTPException, UploadFile
from bson import ObjectId
from typing import Any, Dict, Optional, List
from urllib.parse import quote_plus
import common.db as database
from datetime import datetime
from pathlib import Path
import shutil

DOCUMENT_DEFINITIONS = [
    {
        "id": "presentation",
        "label": "Presentation",
        "description": "Fichiers PDF ou PowerPoint",
        "accept": ".pdf,.ppt,.pptx",
        "extensions": [".pdf", ".ppt", ".pptx"],
    },
    {
        "id": "fiche-synthese",
        "label": "Fiche synthese",
        "description": "Format PDF uniquement",
        "accept": ".pdf",
        "extensions": [".pdf"],
    },
    {
        "id": "rapport",
        "label": "Rapport",
        "description": "Documents Word (.doc, .docx)",
        "accept": ".doc,.docx",
        "extensions": [".doc", ".docx"],
    },
    {
        "id": "notes-mensuelles",
        "label": "Notes mensuelles",
        "description": "Notes mensuelles au format PDF",
        "accept": ".pdf",
        "extensions": [".pdf"],
    },
]

DOCUMENT_COLLECTION_NAME = "journal_documents"
DOCUMENT_STORAGE = Path(__file__).resolve().parent / "storage" / "journal_documents"

COMPETENCY_DEFINITIONS = [
    {
        "id": "C1",
        "title": "C1 Diagnostiquer",
        "description": [
            "Diagnostiquer un systeme numerique existant en vue de le faire evoluer",
            "Diagnostiquer un systeme numerique pour identifier une anomalie",
            "Diagnostiquer un systeme numerique en vue de corriger ou pallier une anomalie",
            "Diagnostiquer un systeme numerique en vue de le maintenir durablement en etat de fonctionnement",
        ],
    },
    {
        "id": "C2",
        "title": "C2 Concevoir",
        "description": [
            "Analyser et construire un cahier des charges",
            "Concevoir l'architecture fonctionnelle ou structurelle d'un systeme numerique en prenant en compte les contraintes de developpement durable",
            "Concevoir un systeme numerique en choisissant des technologies adaptees au besoin defini en tenant compte de l'etat de l'art et des moyens de l'entreprise",
            "Concevoir des systemes numeriques a travers de la modelisation et de la simulation",
        ],
    },
    {
        "id": "C3",
        "title": "C3 Produire",
        "description": [
            "Produire un prototype de systeme numerique",
            "Produire un systeme numerique capable de respecter des contraintes reglementaires, techniques, environnementales et de duree de vie",
        ],
    },
    {
        "id": "C4",
        "title": "C4 Valider",
        "description": [
            "Valider le bon fonctionnement d'un systeme numerique en proposant une demarche visant a identifier l'absence de dysfonctionnement",
            "Valider l'adequation d'une solution avec le cahier des charges",
        ],
    },
    {
        "id": "C5",
        "title": "C5 Piloter",
        "description": [
            "Piloter un projet en assurant la projection et le suivi des actions et du budget",
            "Piloter un projet en manageant une equipe projet pluridisciplinaire et internationale en prenant en compte les aspects techniques humains et economiques",
        ],
    },
    {
        "id": "C6",
        "title": "C6 S'adapter",
        "description": [
            "S'adapter a de nouvelles methodes techniques ou technologies utiles a la conception de systemes numeriques",
            "S'adapter a des contraintes organisationnelles environnementales ou humaines",
            "Anticiper les innovations et evolutions et assurer une veille",
            "Identifier la necessite de se former sur de nouvelles methodes techniques ou technologies",
        ],
    },
    {
        "id": "C7",
        "title": "C7 Communiquer",
        "description": [
            "Communiquer avec des specialistes comme avec des non specialistes en francais et en anglais",
            "Animer et convaincre",
        ],
    },
    {
        "id": "C8",
        "title": "C8 Competence specifique",
        "description": [
            "Competences specifiques definies par l'entreprise (connaissance metiers, normes ou legislation)",
        ],
    },
]

COMPETENCY_LEVELS = [
    {"value": "non_acquis", "label": "Non acquis"},
    {"value": "en_cours", "label": "En cours d'acquisition"},
    {"value": "acquis", "label": "Acquis"},
    {"value": "non_aborde", "label": "Non aborde en entreprise"},
]

COMPETENCY_COLLECTION_NAME = "competency_evaluations"
COMMENTER_ROLES = {
    "tuteur",
    "tuteur_pedagogique",
    "maitre",
    "maitre_apprentissage",
}

def _ensure_storage():
    DOCUMENT_STORAGE.mkdir(parents=True, exist_ok=True)

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

        entretiens = apprenti.get("entretiens") or []
        infos["entretiens"] = sorted(
            entretiens,
            key=lambda item: item.get("date") or "",
            reverse=True,
        )
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


def _documents_collection():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[DOCUMENT_COLLECTION_NAME]


def _promotion_collection():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db["promos"]


def _allowed_extensions(category: str) -> List[str]:
    for definition in DOCUMENT_DEFINITIONS:
        if definition["id"] == category:
            return definition["extensions"]
    raise HTTPException(status_code=400, detail="Categorie de document inconnue")


def _deliverable_definition(deliverable: Dict[str, Any]) -> Dict[str, Any]:
    base = None
    deliverable_id = deliverable.get("deliverable_id") or deliverable.get("id")
    if deliverable_id:
        base = next(
            (
                definition
                for definition in DOCUMENT_DEFINITIONS
                if definition["id"] == deliverable_id
            ),
            None,
        )
    if not deliverable_id and base:
        deliverable_id = base["id"]
    if not deliverable_id:
        deliverable_id = str(ObjectId())
    label = deliverable.get("title") or (base["label"] if base else deliverable_id)
    description = deliverable.get("description") or (base["description"] if base else "")
    due_date = deliverable.get("due_date")
    if due_date:
        description = f"{description} (Echeance : {due_date})".strip()
    accept = base["accept"] if base else ".pdf,.doc,.docx"
    return {
        "id": deliverable_id,
        "label": label,
        "description": description,
        "accept": accept,
    }


async def _retrieve_apprenti_and_promotion(apprenti_id: str):
    apprenti_collection = get_collection("apprenti")
    apprenti = await apprenti_collection.find_one({"_id": ObjectId(apprenti_id)})
    if not apprenti:
        raise HTTPException(status_code=404, detail="Apprenti introuvable")
    promotion_year = apprenti.get("annee_academique")
    if not promotion_year:
        raise HTTPException(status_code=400, detail="Aucune promotion associee a cet apprenti")
    promotion = await _promotion_collection().find_one({"annee_academique": promotion_year})
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion introuvable pour l'apprenti")
    if not promotion.get("semesters"):
        raise HTTPException(status_code=400, detail="La promotion ne contient aucun semestre configure")
    return apprenti, promotion


def _normalize_semester_id(raw: Any) -> str:
    return str(raw) if raw is not None else ""


def _parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _find_deliverable_for_semester(promotion: Dict[str, Any], semester_id: str, key: str) -> Optional[Dict[str, Any]]:
    """Retourne le dict du livrable pour le semestre si le champ deliverable_id/id/title correspond à la clé fournie."""
    for semester in promotion.get("semesters", []):
        current_id = _normalize_semester_id(semester.get("semester_id") or semester.get("id"))
        if current_id != semester_id:
            continue
        for deliverable in semester.get("deliverables", []) or []:
            if str(deliverable.get("deliverable_id") or deliverable.get("id") or "") == str(key):
                return deliverable
            # fallback: match by title (some older records)
            if str(deliverable.get("title") or "") == str(key):
                return deliverable
    return None


def _serialize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(document["_id"])
    comments = [
        {
            "comment_id": comment.get("comment_id"),
            "author_id": comment.get("author_id"),
            "author_name": comment.get("author_name"),
            "author_role": comment.get("author_role"),
            "content": comment.get("content"),
            "created_at": comment.get("created_at"),
        }
        for comment in document.get("comments", [])
    ]
    return {
        "id": doc_id,
        "semester_id": document.get("semester_id"),
        "category": document.get("category"),
        "file_name": document.get("file_name"),
        "file_size": document.get("file_size"),
        "file_type": document.get("file_type"),
        "uploaded_at": document.get("uploaded_at"),
        "uploader_id": document.get("uploader", {}).get("id"),
        "uploader_name": document.get("uploader", {}).get("name"),
        "uploader_role": document.get("uploader", {}).get("role"),
        "download_url": f"/apprenti/documents/{doc_id}/download",
        "comments": comments,
    }


async def list_journal_documents(apprenti_id: str) -> Dict[str, Any]:
    _, promotion = await _retrieve_apprenti_and_promotion(apprenti_id)
    collection = _documents_collection()
    documents = await collection.find({"apprentice_id": apprenti_id}).to_list(length=None)
    documents_by_semester: Dict[str, List[Dict[str, Any]]] = {}
    for document in documents:
        semester_id = document.get("semester_id")
        documents_by_semester.setdefault(semester_id, []).append(_serialize_document(document))

    semesters_payload = []
    for semester in sorted(promotion.get("semesters", []), key=lambda entry: entry.get("order", 0)):
        semester_id = _normalize_semester_id(semester.get("semester_id") or semester.get("id"))
        if not semester_id:
            continue
        deliverables_source = semester.get("deliverables") or []
        deliverables_payload = [
            _deliverable_definition(deliverable) for deliverable in deliverables_source
        ]
        semesters_payload.append(
            {
                "semester_id": semester_id,
                "name": semester.get("name") or semester_id,
                "deliverables": deliverables_payload,
                "documents": documents_by_semester.get(semester_id, []),
            }
        )

    promotion_summary = {
        "promotion_id": str(promotion["_id"]),
        "annee_academique": promotion.get("annee_academique"),
        "label": promotion.get("label"),
    }
    categories = [
        {
            "id": definition["id"],
            "label": definition["label"],
            "description": definition["description"],
            "accept": definition["accept"],
        }
        for definition in DOCUMENT_DEFINITIONS
    ]
    return {
        "promotion": promotion_summary,
        "semesters": semesters_payload,
        "categories": categories,
    }


def _resolve_semester(promotion: Dict[str, Any], semester_id: str) -> Dict[str, Any]:
    for semester in promotion.get("semesters", []):
        current_id = _normalize_semester_id(semester.get("semester_id") or semester.get("id"))
        if current_id == semester_id:
            return semester
    raise HTTPException(status_code=404, detail="Semestre introuvable pour cette promotion")


def _build_storage_path(promotion_id: str, semester_id: str, document_id: str, extension: str) -> Path:
    _ensure_storage()
    target_dir = DOCUMENT_STORAGE / promotion_id / semester_id
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"{document_id}{extension}"


async def create_journal_document(
    apprenti_id: str,
    *,
    category: str,
    semester_id: str,
    uploader_id: str,
    uploader_name: str,
    uploader_role: str,
    upload: UploadFile,
) -> Dict[str, Any]:
    # Récupère l'apprenti et la promotion associée (nécessaire pour valider semestre, stockage)
    apprenti, promotion = await _retrieve_apprenti_and_promotion(apprenti_id)
    semester_id = semester_id.strip()
    if not semester_id:
        raise HTTPException(status_code=400, detail="Semestre requis")
    _resolve_semester(promotion, semester_id)

    # Empêche le dépôt si un livrable correspondant à cette catégorie/ID existe
    # pour le semestre et que sa date d'echeance est depassee.
    matching = _find_deliverable_for_semester(promotion, semester_id, category)
    if matching:
        due_val = matching.get("due_date")
        due_dt = _parse_iso_date(due_val)
        if due_dt and datetime.utcnow() > due_dt:
            raise HTTPException(status_code=400, detail=f"Depot refuse : livrable '{matching.get('title') or category}' ferme depuis {due_val}")
    # Vérifie l'extension autorisée pour la catégorie de document
    allowed_extensions = _allowed_extensions(category)
    original_name = upload.filename or "document"
    extension = Path(original_name).suffix.lower()
    if extension not in allowed_extensions:
        # Rejette le fichier si l'extension n'est pas dans la liste blanche
        raise HTTPException(status_code=400, detail="Extension de fichier non autorisee pour ce type")

    # Génère un nouvel identifiant pour le document et prépare le chemin de stockage
    document_id = ObjectId()
    promotion_id = str(promotion["_id"])
    file_path = _build_storage_path(promotion_id, semester_id, str(document_id), extension)

    # Écrit le fichier reçu sur le disque dans l'emplacement prévu
    # Utilise un write binaire et copie le flux pour éviter de charger tout le fichier en mémoire
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    # Construit l'enregistrement qui sera inséré en base de données pour référencer le fichier
    document_record = {
        "_id": document_id,
        "apprentice_id": apprenti_id,
        "apprentice_name": _build_full_name(apprenti),
        "promotion_id": promotion_id,
        "semester_id": semester_id,
        "category": category,
        "file_name": original_name,
        "file_size": file_path.stat().st_size,
        "file_type": upload.content_type or "application/octet-stream",
        # On stocke le chemin relatif pour faciliter les moves de `DOCUMENT_STORAGE`
        "file_path": str(file_path.relative_to(DOCUMENT_STORAGE)),
        "uploaded_at": datetime.utcnow(),
        "uploader": {
            "id": uploader_id,
            "name": uploader_name,
            "role": uploader_role,
        },
        "comments": [],
    }

    # Insert le méta-document en base (le fichier est déjà écrit sur disque)
    await _documents_collection().insert_one(document_record)
    # Envoie une notification et un e-mail au titulaire de l'apprenti (si email present)
    try:
        from common.notifications import create_notification, notify_user_via_email
        # notification pour l'apprenti
        await create_notification(apprenti_id, f"Nouveau document de type {category} depose: {original_name}", {"document_id": str(document_id)})
        # envoi d'e-mail (best-effort)
        notify_user_via_email(apprenti.get("email"), "Nouveau document depose", f"Un nouveau document ({original_name}) a ete depose pour vous dans la promotion {promotion.get('annee_academique')}")
    except Exception:
        pass
    # Retourne la représentation sérialisée côté API
    return _serialize_document(document_record)


async def update_journal_document(
    apprenti_id: str,
    document_id: str,
    upload: UploadFile,
) -> Dict[str, Any]:
    documents_collection = _documents_collection()
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if document.get("apprentice_id") != apprenti_id:
        raise HTTPException(status_code=403, detail="Document non associe a cet apprenti")

    # Bloque la mise a jour du document si le livrable associe au semestre a une date d'echeance depassee
    promo_apprenti, promotion = await _retrieve_apprenti_and_promotion(apprenti_id)
    matching = _find_deliverable_for_semester(promotion, document.get("semester_id"), document.get("category"))
    if matching:
        due_val = matching.get("due_date")
        due_dt = _parse_iso_date(due_val)
        if due_dt and datetime.utcnow() > due_dt:
            raise HTTPException(status_code=400, detail=f"Mise a jour refusee : livrable '{matching.get('title') or document.get('category')}' ferme depuis {due_val}")

    allowed_extensions = _allowed_extensions(document.get("category"))
    original_name = upload.filename or document.get("file_name") or "document"
    extension = Path(original_name).suffix.lower()
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Extension de fichier non autorisee pour ce type")

    promotion_id = document.get("promotion_id")
    semester_id = document.get("semester_id")
    file_path = _build_storage_path(promotion_id, semester_id, document_id, extension)
    # Écrit le nouveau fichier sur le disque (remplace l'ancien fichier)
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    # Si un ancien fichier était présent, on le supprime pour éviter de laisser des orphelins
    previous_relative_path = document.get("file_path")
    if previous_relative_path:
        old_path = DOCUMENT_STORAGE / previous_relative_path
        if old_path.exists() and old_path != file_path:
            old_path.unlink(missing_ok=True)

    # Met à jour les métadonnées du document en base (taille, type, chemin, date)
    updates = {
        "file_name": original_name,
        "file_size": file_path.stat().st_size,
        "file_type": upload.content_type or document.get("file_type"),
        "file_path": str(file_path.relative_to(DOCUMENT_STORAGE)),
        "uploaded_at": datetime.utcnow(),
    }
    await documents_collection.update_one({"_id": document["_id"]}, {"$set": updates})
    document.update(updates)
    return _serialize_document(document)


async def add_document_comment(
    apprenti_id: str,
    document_id: str,
    *,
    author_id: str,
    author_name: str,
    author_role: str,
    content: str,
) -> Dict[str, Any]:
    document = await _documents_collection().find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if document.get("apprentice_id") != apprenti_id:
        raise HTTPException(status_code=403, detail="Document non associe a cet apprenti")

    normalized_role = author_role.lower()
    if normalized_role not in COMMENTER_ROLES:
        raise HTTPException(status_code=403, detail="Ce role ne peut pas commenter les documents")
    message = content.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Commentaire vide")

    comment = {
        "comment_id": str(ObjectId()),
        "author_id": author_id,
        "author_name": author_name,
        "author_role": author_role,
        "content": message,
        "created_at": datetime.utcnow(),
    }
    await _documents_collection().update_one(
        {"_id": document["_id"]},
        {"$push": {"comments": comment}},
    )
    return comment


async def get_document_file(document_id: str) -> tuple[Path, str, str]:
    document = await _documents_collection().find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")
    relative_path = document.get("file_path")
    if not relative_path:
        raise HTTPException(status_code=500, detail="Chemin du document invalide")
    file_path = DOCUMENT_STORAGE / relative_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable sur le serveur")
    return file_path, document.get("file_name") or file_path.name, document.get("file_type") or "application/octet-stream"


def _competency_collection():
    if database.db is None:
        raise HTTPException(status_code=500, detail="Connexion DB absente")
    return database.db[COMPETENCY_COLLECTION_NAME]


async def list_competency_evaluations(apprenti_id: str) -> Dict[str, Any]:
    apprenti, promotion = await _retrieve_apprenti_and_promotion(apprenti_id)
    collection = _competency_collection()
    record = await collection.find_one({"apprentice_id": apprenti_id})
    stored_evaluations: Dict[str, Dict[str, str]] = record.get("evaluations", {}) if record else {}

    semesters_payload = []
    for semester in sorted(promotion.get("semesters", []), key=lambda entry: entry.get("order", 0)):
        semester_id = _normalize_semester_id(semester.get("semester_id") or semester.get("id"))
        if not semester_id:
            continue
        evaluations_for_semester = stored_evaluations.get(semester_id, {})
        competencies_payload = [
            {
                "competency_id": definition["id"],
                "level": evaluations_for_semester.get(definition["id"]),
            }
            for definition in COMPETENCY_DEFINITIONS
        ]
        semesters_payload.append(
            {
                "semester_id": semester_id,
                "name": semester.get("name") or semester_id,
                "competencies": competencies_payload,
            }
        )

    promotion_summary = {
        "promotion_id": str(promotion["_id"]),
        "annee_academique": promotion.get("annee_academique"),
        "label": promotion.get("label"),
    }
    return {
        "promotion": promotion_summary,
        "semesters": semesters_payload,
        "competencies": [
            {
                "id": definition["id"],
                "title": definition["title"],
                "description": definition["description"],
            }
            for definition in COMPETENCY_DEFINITIONS
        ],
        "levels": COMPETENCY_LEVELS,
    }


async def update_competency_evaluations(apprenti_id: str, semester_id: str, entries: List[Dict[str, str]]) -> Dict[str, Any]:
    semester_id = semester_id.strip()
    if not semester_id:
        raise HTTPException(status_code=400, detail="Semestre requis")
    _, promotion = await _retrieve_apprenti_and_promotion(apprenti_id)
    _resolve_semester(promotion, semester_id)

    valid_competency_ids = {definition["id"] for definition in COMPETENCY_DEFINITIONS}
    valid_levels = {level["value"] for level in COMPETENCY_LEVELS}

    normalized_entries: Dict[str, str] = {}
    for entry in entries:
        competency_id = entry.get("competency_id")
        level = entry.get("level")
        if competency_id not in valid_competency_ids:
            raise HTTPException(status_code=400, detail="Competence inconnue")
        if level not in valid_levels:
            raise HTTPException(status_code=400, detail="Niveau de competence invalide")
        normalized_entries[competency_id] = level

    collection = _competency_collection()
    await collection.update_one(
        {"apprentice_id": apprenti_id},
        {
            "$set": {
                "apprentice_id": apprenti_id,
                "promotion_id": str(promotion["_id"]),
                f"evaluations.{semester_id}": normalized_entries,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )

    return await list_competency_evaluations(apprenti_id)
