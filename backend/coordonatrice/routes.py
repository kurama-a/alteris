from fastapi import APIRouter

from coordonatrice.models import HealthResponse, User, UserUpdate
from coordonatrice.functions import (
    creer_coordonatrice,
    mettre_a_jour_coordonatrice,
    supprimer_coordonatrice,
)

coordonatrice_api = APIRouter(tags=["Coordonatrice"])


@coordonatrice_api.get("/profile")
def get_profile():
    return {"message": "Données du profil coordonatrice"}


@coordonatrice_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "coordonatrice"}


@coordonatrice_api.post("/", tags=["Coordonatrice"])
async def create_coordonatrice(payload: User):
    return await creer_coordonatrice(payload)


@coordonatrice_api.put("/{coordonatrice_id}", tags=["Coordonatrice"])
async def update_coordonatrice(coordonatrice_id: str, payload: UserUpdate):
    return await mettre_a_jour_coordonatrice(coordonatrice_id, payload)


@coordonatrice_api.delete("/{coordonatrice_id}", tags=["Coordonatrice"])
async def delete_coordonatrice(coordonatrice_id: str):
    return await supprimer_coordonatrice(coordonatrice_id)
