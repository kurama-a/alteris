from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
class HealthResponse(BaseModel):
    status: str
    service: str


class User(BaseModel):
    name: str = Field(..., example="Jean Dupont")
    email: EmailStr = Field(..., example="jean.dupont@example.com")
    age: Optional[int] = Field(None, example=25)


class CreerEntretienRequest(BaseModel):
    apprenti_id: str
    date: datetime
    sujet: str