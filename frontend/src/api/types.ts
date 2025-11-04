// frontend/src/api/types.ts

export interface LoginRequest {
  email: string;
  password: string;
  profil: string;
}

export interface LoginResponse {
  access_token: string;
}

export interface EmailRequest {
  prenom: string;
  nom: string;
  profil: string;
}

export interface EmailResponse {
  email: string;
  password: string;
  profil: string;
}