import type { ComputeResponse, Observation } from './types';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

let authToken: string | null = localStorage.getItem('authToken');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('authToken', token);
  } else {
    localStorage.removeItem('authToken');
  }
}

export function getAuthToken() {
  return authToken;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Ошибка запроса');
  }
  return response.json() as Promise<T>;
}

export async function fetchObservations(): Promise<Observation[]> {
  const res = await fetch(`${API_URL}/observations`);
  return handleResponse<Observation[]>(res);
}

export async function submitObservation(formData: FormData): Promise<Observation> {
  const headers: Record<string, string> = {};
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  const res = await fetch(`${API_URL}/observations`, {
    method: 'POST',
    body: formData,
    headers,
  });
  return handleResponse<Observation>(res);
}

export async function deleteObservation(id: number): Promise<void> {
  const headers: Record<string, string> = {};
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  const res = await fetch(`${API_URL}/observations/${id}`, { method: 'DELETE', headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Не удалось удалить наблюдение');
  }
}

export async function requestComputation(): Promise<ComputeResponse> {
  const headers: Record<string, string> = {};
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  const res = await fetch(`${API_URL}/compute`, { method: 'POST', headers });
  return handleResponse<ComputeResponse>(res);
}

export async function login(username: string, password: string) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const res = await fetch(`${API_URL}/login`, {
    method: 'POST',
    body: form,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return handleResponse<{ access_token: string; token_type: string }>(res);
}
