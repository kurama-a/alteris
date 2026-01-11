from fastapi import APIRouter

from entreprise.models import Entity, EntityUpdate, HealthResponse
from entreprise.functions import (
    creer_entreprise,
    lister_entreprises,
    mettre_a_jour_entreprise,
    recuperer_infos_entreprise_completes,
    supprimer_entreprise,
)

entreprise_api = APIRouter(tags=["Entreprise"])


@entreprise_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "entreprise"}


@entreprise_api.get("/", tags=["Entreprise"])
async def list_entreprises():
    return await lister_entreprises()


@entreprise_api.get("/infos-completes/{entreprise_id}", tags=["Entreprise"])
async def get_entreprise_infos_completes(entreprise_id: str):
    return await recuperer_infos_entreprise_completes(entreprise_id)


@entreprise_api.post("/", tags=["Entreprise"])
async def create_entreprise(payload: Entity):
    return await creer_entreprise(payload)


@entreprise_api.put("/{entreprise_id}", tags=["Entreprise"])
async def update_entreprise(entreprise_id: str, payload: EntityUpdate):
    return await mettre_a_jour_entreprise(entreprise_id, payload)


@entreprise_api.delete("/{entreprise_id}", tags=["Entreprise"])
async def delete_entreprise(entreprise_id: str):
    return await supprimer_entreprise(entreprise_id)
