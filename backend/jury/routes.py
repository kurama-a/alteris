from datetime import datetime
from typing import Dict, List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

import common.db as database
from jury.models import (
    HealthResponse,
    JuryCreateRequest,
    JuryMembers,
    JuryResponse,
    JuryStatus,
    JuryUpdateRequest,
    MemberDetails,
)

jury_api = APIRouter(tags=["Jury"])

JURY_COLLECTION = "juries"

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


def _parse_object_id(identifier: str) -> ObjectId:
    try:
        return ObjectId(identifier)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Identifiant invalide")


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
    return JuryResponse(
        id=str(document.get("_id")),
        semestre_reference=document.get("semestre_reference"),
        date=document.get("date"),
        status=JuryStatus(status_value),
        members=_serialize_members(document.get("members", {})),
        created_at=document.get("created_at"),
        updated_at=document.get("updated_at"),
    )


async def _get_jury_or_404(jury_id: str) -> dict:
    document = await _jury_collection().find_one({"_id": _parse_object_id(jury_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Jury introuvable")
    return document


@jury_api.get("/profile")
def get_profile():
    return {"message": "Donnees du profil jury"}


@jury_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "jury"}


@jury_api.post("/juries", response_model=JuryResponse, summary="Creer un jury")
async def create_jury(payload: JuryCreateRequest):
    members = await _build_members(payload)
    now = datetime.utcnow()
    document = {
        "semestre_reference": payload.semestre_reference,
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

    if payload.semestre_reference is not None:
        updates["semestre_reference"] = payload.semestre_reference
    if payload.date is not None:
        updates["date"] = payload.date
    if payload.status is not None:
        updates["status"] = payload.status.value

    updated_members = await _apply_member_updates(payload, current_document.get("members", {}))
    if updated_members != current_document.get("members", {}):
        updates["members"] = updated_members

    if not updates:
        return _serialize_jury(current_document)

    updates["updated_at"] = datetime.utcnow()
    await _jury_collection().update_one({"_id": current_document["_id"]}, {"$set": updates})
    current_document.update(updates)
    return _serialize_jury(current_document)
