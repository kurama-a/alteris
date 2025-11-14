from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class User(BaseModel):
    first_name: str = Field(..., example="Sophie")
    last_name: str = Field(..., example="Martin")
    email: EmailStr = Field(..., example="sophie.martin@example.com")
    phone: Optional[str] = Field(None, example="+33601020304")
    role: str = Field(default="responsable_formation", example="responsable_formation")


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(default=None, example="responsable_formation")
