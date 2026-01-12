// src/api/auth.ts
import axios from "axios";
import type { EmailRequest, EmailResponse, LoginRequest, LoginResponse } from "./types";
import { AUTH_API_URL } from "../config";

export async function generateEmail(data: EmailRequest): Promise<EmailResponse> {
  const res = await axios.post(`${API}/auth/generate-email`, data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await axios.post(`${AUTH_API_URL}/login`, data);
  return response.data;
}