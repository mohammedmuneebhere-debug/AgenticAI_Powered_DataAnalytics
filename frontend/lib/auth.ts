"use client";

import { API_URL } from "./api";

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

const TOKEN_KEY = "socialiq-token";
const USER_KEY = "socialiq-user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function storeSession(response: AuthResponse): void {
  window.localStorage.setItem(TOKEN_KEY, response.access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(response.user));
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

async function authRequest(path: string, body: Record<string, unknown>): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `Authentication failed (${res.status})`;
    try {
      const payload = await res.json();
      if (payload?.detail) detail = payload.detail;
    } catch {
      // keep default message
    }
    throw new Error(detail);
  }
  const data = (await res.json()) as AuthResponse;
  storeSession(data);
  return data;
}

export function register(email: string, name: string, password: string): Promise<AuthResponse> {
  return authRequest("/auth/register", { email, name, password });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return authRequest("/auth/login", { email, password });
}

export function logout(): void {
  clearSession();
  window.location.href = "/login";
}

export async function fetchCurrentUser(token: string): Promise<User> {
  const res = await fetch(`${API_URL}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    clearSession();
    throw new Error("Session expired");
  }
  return res.json();
}
