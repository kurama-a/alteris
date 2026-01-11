from fastapi import APIRouter

from responsable_cursus.models import HealthResponse, User, UserUpdate
from .functions import (
    creer_responsable_cursus,
    mettre_a_jour_responsable_cursus,
    recuperer_infos_responsable_cursus_completes,
    supprimer_responsable_cursus,
)

responsable_cursus_api = APIRouter(tags=["responsable_cursus"])


@responsable_cursus_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "responsable_cursus"}


@responsable_cursus_api.get("/infos-completes/{responsable_cursus_id}", tags=["responsable_cursus"])
async def get_responsable_cursus_infos_completes(responsable_cursus_id: str):
    return await recuperer_infos_responsable_cursus_completes(responsable_cursus_id)


@responsable_cursus_api.post("/", tags=["responsable_cursus"])
async def create_responsable_cursus(payload: User):
    return await creer_responsable_cursus(payload)


@responsable_cursus_api.put("/{responsable_cursus_id}", tags=["responsable_cursus"])
async def update_responsable_cursus(responsable_cursus_id: str, payload: UserUpdate):
    return await mettre_a_jour_responsable_cursus(responsable_cursus_id, payload)


@responsable_cursus_api.delete("/{responsable_cursus_id}", tags=["responsable_cursus"])
async def delete_responsable_cursus(responsable_cursus_id: str):
    return await supprimer_responsable_cursus(responsable_cursus_id)
