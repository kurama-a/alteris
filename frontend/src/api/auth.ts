// src/api/auth.ts
import axios from "axios";
import type { EmailRequest, EmailResponse, LoginRequest, LoginResponse } from "./types";
const API = import.meta.env.VITE_API_BASE_URL;

export async function generateEmail(data: EmailRequest): Promise<EmailResponse> {
  const res = await axios.post(`${API}/auth/generate-email`, data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await axios.post("http://localhost:8000/auth/login", data);
  return response.data;
}