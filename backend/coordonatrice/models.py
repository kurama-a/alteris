from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class User(BaseModel):
    first_name: str = Field(..., example="Claire")
    last_name: str = Field(..., example="Martin")
    email: EmailStr = Field(..., example="claire.martin@example.com")
    phone: Optional[str] = Field(None, example="+33102030405")
    role: str = Field(default="coordonatrice", example="coordonatrice")


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(default=None, example="coordonatrice")
