from pydantic import BaseModel, Field, EmailStr
from typing import Optional
class HealthResponse(BaseModel):
    status: str
    service: str


class User(BaseModel):
    name: str = Field(..., example="Jean Dupont")
    email: EmailStr = Field(..., example="jean.dupont@example.com")
    age: Optional[int] = Field(None, example=25)