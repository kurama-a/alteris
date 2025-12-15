from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

import common.db as database
from jury.models import (
    HealthResponse,
    JuryCreateRequest,
    JuryMembers,
    JuryPromotionReference,
    JuryPromotionTimelineOption,
    JuryResponse,
    JuryStatus,
    JuryUpdateRequest,
    MemberDetails,
    TimelineDeliverableOption,
    TimelineSemesterOption,
)

jury_api = APIRouter(tags=["Jury"])

JURY_COLLECTION = "juries"
PROMOTION_COLLECTION = "promos"

MEMBER_SOURCES: Dict[str, Dict[str, str]] = {
    "tuteur": {
        "collection": "users_tuteur_pedagogique",
        "label": "Tuteur pedagogique",
        "role": "tuteur_pedagogique",
    },
    "professeur": {
        "collection": "users_professeur",
        "label": "Professeur",
        "role": "professeur",
    },
    "apprenti": {
        "collection": "users_apprenti",
        "label": "Apprenti",
        "role": "apprenti",
    },
    "intervenant": {
        "collection": "users_intervenant",
        "label": "Intervenant",
        "role": "intervenant",
    },
}


def _get_collection(name: str):
    if database.db is None:
        raise HTTPException(status_code=500, detail="DB non initialisee")
    return database.db[name]


def _jury_collection():
    return _get_collection(JURY_COLLECTION)


def _promotion_collection():
    return _get_collection(PROMOTION_COLLECTION)


def _parse_object_id(identifier: str) -> ObjectId:
    try:
        return ObjectId(identifier)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Identifiant invalide")


def _normalize_optional_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


async def _load_member(member_key: str, user_id: str) -> MemberDetails:
    source = MEMBER_SOURCES[member_key]
    collection = _get_collection(source["collection"])
    document = await collection.find_one({"_id": _parse_object_id(user_id)})
    if not document:
        raise HTTPException(status_code=404, detail=f"{source['label']} introuvable")

    return MemberDetails(
        user_id=str(document["_id"]),
        role=source["role"],
        first_name=document.get("first_name"),
        last_name=document.get("last_name"),
        email=document.get("email"),
        phone=document.get("phone"),
    )


async def _build_members(payload: JuryCreateRequest) -> Dict[str, Dict]:
    return {
        key: (await _load_member(key, getattr(payload, f"{key}_id"))).model_dump()
        for key in MEMBER_SOURCES.keys()
    }


async def _apply_member_updates(
    payload: JuryUpdateRequest, current_members: Dict[str, Dict]
) -> Dict[str, Dict]:
    updated_members = dict(current_members)
    changed = False
    for key in MEMBER_SOURCES.keys():
        user_id = getattr(payload, f"{key}_id", None)
        if user_id is None:
            continue
        updated_members[key] = (await _load_member(key, user_id)).model_dump()
        changed = True
    return updated_members if changed else current_members


def _serialize_members(raw_members: Dict[str, Dict]) -> JuryMembers:
    try:
        return JuryMembers(
            tuteur=MemberDetails(**raw_members["tuteur"]),
            professeur=MemberDetails(**raw_members["professeur"]),
            apprenti=MemberDetails(**raw_members["apprenti"]),
            intervenant=MemberDetails(**raw_members["intervenant"]),
        )
    except KeyError:
        raise HTTPException(status_code=500, detail="Jury invalide en base de donnees")


def _serialize_jury(document: dict) -> JuryResponse:
    status_value = document.get("status", JuryStatus.planifie.value)
    promotion_reference = document.get("promotion_reference")
    serialized_reference: Optional[JuryPromotionReference] = None
    if promotion_reference:
        serialized_reference = JuryPromotionReference(**promotion_reference)
    return JuryResponse(
        id=str(document.get("_id")),
        semestre_reference=document.get("semestre_reference") or "",
        date=document.get("date"),
        status=JuryStatus(status_value),
        members=_serialize_members(document.get("members", {})),
        created_at=document.get("created_at"),
        updated_at=document.get("updated_at"),
        promotion_reference=serialized_reference,
    )


async def _get_jury_or_404(jury_id: str) -> dict:
    document = await _jury_collection().find_one({"_id": _parse_object_id(jury_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Jury introuvable")
    return document


async def _load_promotion_document(promotion_id: str) -> dict:
    document = await _promotion_collection().find_one({"_id": _parse_object_id(promotion_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Promotion introuvable")
    return document


def _match_semester(document: dict, semester_id: str) -> dict:
    for semester in document.get("semesters", []):
        current_id = str(semester.get("semester_id") or semester.get("id") or "")
        if current_id == semester_id:
            return semester
    raise HTTPException(status_code=404, detail="Semestre introuvable pour cette promotion")


def _match_deliverable(semester: dict, deliverable_id: Optional[str]) -> Optional[dict]:
    if not deliverable_id:
        return None
    for deliverable in semester.get("deliverables", []):
        current_id = str(deliverable.get("deliverable_id") or deliverable.get("id") or "")
        if current_id == deliverable_id:
            return deliverable
    raise HTTPException(status_code=404, detail="Livrable introuvable pour ce semestre")


async def _build_promotion_reference(
    promotion_id: str, semester_id: str, deliverable_id: Optional[str]
) -> Tuple[JuryPromotionReference, str]:
    promotion_doc = await _load_promotion_document(promotion_id)
    semester_doc = _match_semester(promotion_doc, semester_id)
    deliverable_doc = _match_deliverable(semester_doc, deliverable_id)

    promotion_reference = JuryPromotionReference(
        promotion_id=str(promotion_doc["_id"]),
        annee_academique=promotion_doc.get("annee_academique"),
        label=promotion_doc.get("label"),
        semester_id=semester_id,
        semester_name=semester_doc.get("name"),
        deliverable_id=deliverable_doc.get("deliverable_id") if deliverable_doc else None,
        deliverable_title=deliverable_doc.get("title") if deliverable_doc else None,
    )
    semester_name = promotion_reference.semester_name
    if not semester_name:
        raise HTTPException(status_code=400, detail="Le semestre selectionne est invalide")
    return promotion_reference, semester_name


@jury_api.get("/profile")
def get_profile():
    return {"message": "Donnees du profil jury"}


@jury_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "jury"}


@jury_api.get(
    "/promotions-timeline",
    response_model=List[JuryPromotionTimelineOption],
    summary="Lister les promotions et semestres disponibles",
)
async def list_promotion_timelines():
    cursor = _promotion_collection().find().sort("annee_academique", 1)
    options: List[JuryPromotionTimelineOption] = []
    async for promotion in cursor:
        annee = promotion.get("annee_academique")
        if not annee:
            continue
        semesters: List[TimelineSemesterOption] = []
        for semester in sorted(promotion.get("semesters", []), key=lambda entry: entry.get("order", 0)):
            semester_id = semester.get("semester_id") or semester.get("id")
            name = semester.get("name")
            if not semester_id or not name:
                continue
            deliverables = [
                TimelineDeliverableOption(
                    deliverable_id=str(deliverable.get("deliverable_id") or deliverable.get("id")),
                    title=deliverable.get("title"),
                    due_date=deliverable.get("due_date"),
                )
                for deliverable in sorted(semester.get("deliverables", []), key=lambda entry: entry.get("order", 0))
                if deliverable.get("title")
            ]
            semesters.append(
                TimelineSemesterOption(
                    semester_id=str(semester_id),
                    name=name,
                    deliverables=deliverables,
                )
            )
        if semesters:
            options.append(
                JuryPromotionTimelineOption(
                    promotion_id=str(promotion["_id"]),
                    annee_academique=annee,
                    label=promotion.get("label"),
                    semesters=semesters,
                )
            )
    return options


@jury_api.post("/juries", response_model=JuryResponse, summary="Creer un jury")
async def create_jury(payload: JuryCreateRequest):
    members = await _build_members(payload)
    deliverable_id = _normalize_optional_id(payload.deliverable_id)
    promotion_reference, semester_name = await _build_promotion_reference(
        payload.promotion_id, payload.semester_id, deliverable_id
    )
    now = datetime.utcnow()
    document = {
        "promotion_reference": promotion_reference.model_dump(),
        "semestre_reference": semester_name,
        "date": payload.date,
        "status": payload.status.value,
        "members": members,
        "created_at": now,
        "updated_at": now,
    }
    insert_result = await _jury_collection().insert_one(document)
    document["_id"] = insert_result.inserted_id
    return _serialize_jury(document)


@jury_api.get("/juries", response_model=List[JuryResponse], summary="Lister les juries")
async def list_juries():
    cursor = _jury_collection().find().sort("date", 1)
    return [_serialize_jury(document) async for document in cursor]


@jury_api.get("/juries/{jury_id}", response_model=JuryResponse, summary="Recuperer un jury")
async def get_jury(jury_id: str):
    document = await _get_jury_or_404(jury_id)
    return _serialize_jury(document)


@jury_api.get("/infos-completes/{jury_id}", response_model=JuryResponse, tags=["Jury"])
async def get_jury_infos_completes(jury_id: str):
    return await get_jury(jury_id)


@jury_api.patch("/juries/{jury_id}", response_model=JuryResponse, summary="Mettre a jour un jury")
async def update_jury(jury_id: str, payload: JuryUpdateRequest):
    current_document = await _get_jury_or_404(jury_id)
    updates: Dict[str, object] = {}

    if payload.date is not None:
        updates["date"] = payload.date
    if payload.status is not None:
        updates["status"] = payload.status.value

    deliverable_id = _normalize_optional_id(payload.deliverable_id)
    needs_timeline_update = any(
        value is not None for value in (payload.promotion_id, payload.semester_id, deliverable_id)
    )

    if needs_timeline_update or not current_document.get("promotion_reference"):
        base_reference = current_document.get("promotion_reference") or {}
        promotion_id = payload.promotion_id or base_reference.get("promotion_id")
        semester_id = payload.semester_id or base_reference.get("semester_id")
        if not promotion_id or not semester_id:
            raise HTTPException(status_code=400, detail="Promotion et semestre requis pour mettre a jour le jury")
        promotion_reference, semester_name = await _build_promotion_reference(
            promotion_id, semester_id, deliverable_id or base_reference.get("deliverable_id")
        )
        updates["promotion_reference"] = promotion_reference.model_dump()
        updates["semestre_reference"] = semester_name

    updated_members = await _apply_member_updates(payload, current_document.get("members", {}))
    if updated_members != current_document.get("members", {}):
        updates["members"] = updated_members

    if not updates:
        return _serialize_jury(current_document)

    updates["updated_at"] = datetime.utcnow()
    await _jury_collection().update_one({"_id": current_document["_id"]}, {"$set": updates})
    current_document.update(updates)
    return _serialize_jury(current_document)
