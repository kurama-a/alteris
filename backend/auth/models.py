from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    email: EmailStr
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None


class EmailRequest(BaseModel):
    nom: str
    prenom: str
    profil: str


class PasswordRecoveryRequest(BaseModel):
    email: str
    profil: str

 
class LoginRequest(BaseModel):
    email: str
    password: str
    profil: str