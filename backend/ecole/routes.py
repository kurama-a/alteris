from fastapi import APIRouter

from ecole.models import Entity, EntityUpdate, HealthResponse
from functions import (
    creer_ecole,
    mettre_a_jour_ecole,
    recuperer_infos_ecole_completes,
    supprimer_ecole,
)

ecole_api = APIRouter(tags=["Ecole"])


@ecole_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "ecole"}


@ecole_api.get("/infos-completes/{ecole_id}", tags=["Ecole"])
async def get_ecole_infos_completes(ecole_id: str):
    return await recuperer_infos_ecole_completes(ecole_id)


@ecole_api.post("/", tags=["Ecole"])
async def create_ecole(payload: Entity):
    return await creer_ecole(payload)


@ecole_api.put("/{ecole_id}", tags=["Ecole"])
async def update_ecole(ecole_id: str, payload: EntityUpdate):
    return await mettre_a_jour_ecole(ecole_id, payload)


@ecole_api.delete("/{ecole_id}", tags=["Ecole"])
async def delete_ecole(ecole_id: str):
    return await supprimer_ecole(ecole_id)
