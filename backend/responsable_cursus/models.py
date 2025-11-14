from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class User(BaseModel):
    first_name: str = Field(..., example="Julien")
    last_name: str = Field(..., example="Bernard")
    email: EmailStr = Field(..., example="julien.bernard@example.com")
    phone: Optional[str] = Field(None, example="+33601020304")
    role: str = Field(default="responsable_cursus", example="responsable_cursus")


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(default=None, example="responsable_cursus")
