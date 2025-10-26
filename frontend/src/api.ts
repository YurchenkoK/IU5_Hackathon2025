import type { ComputeResponse, Observation } from './types';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// Token management
const TOKEN_KEY = 'comet_auth_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// Fetch with auth
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return fetch(url, { ...options, headers });
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Ошибка запроса');
  }
  return response.json() as Promise<T>;
}

// Auth API
export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export async function register(data: RegisterData): Promise<UserResponse> {
  const res = await fetch(`${API_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<UserResponse>(res);
}

export async function login(data: LoginData): Promise<TokenResponse> {
  const res = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const tokenData = await handleResponse<TokenResponse>(res);
  setToken(tokenData.access_token);
  return tokenData;
}

export async function logout(): Promise<void> {
  removeToken();
}

export async function getCurrentUser(): Promise<UserResponse> {
  const res = await fetchWithAuth(`${API_URL}/me`);
  return handleResponse<UserResponse>(res);
}

// Observations API
export async function fetchObservations(): Promise<Observation[]> {
  const res = await fetch(`${API_URL}/observations`);
  return handleResponse<Observation[]>(res);
}

export async function submitObservation(formData: FormData): Promise<Observation> {
  const res = await fetchWithAuth(`${API_URL}/observations`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<Observation>(res);
}

export async function deleteObservation(id: number): Promise<void> {
  const res = await fetchWithAuth(`${API_URL}/observations/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Не удалось удалить наблюдение');
  }
}

export async function requestComputation(): Promise<ComputeResponse> {
  const res = await fetchWithAuth(`${API_URL}/compute`, { method: 'POST' });
  return handleResponse<ComputeResponse>(res);
}
