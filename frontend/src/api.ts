import type { ComputeResponse, Observation } from './types';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// Управление токеном
let authToken: string | null = localStorage.getItem('authToken');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('authToken', token);
  } else {
    localStorage.removeItem('authToken');
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {};
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      // Токен истек или невалиден
      setAuthToken(null);
      throw new Error('Требуется авторизация');
    }
    const detail = await response.text();
    throw new Error(detail || 'Ошибка запроса');
  }
  return response.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<string> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Неверный логин или пароль');
  }

  const data = await res.json();
  const token = data.access_token;
  setAuthToken(token);
  return token;
}

export function logout() {
  setAuthToken(null);
}

export async function fetchObservations(): Promise<Observation[]> {
  const res = await fetch(`${API_URL}/observations`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<Observation[]>(res);
}

export async function submitObservation(formData: FormData): Promise<Observation> {
  const res = await fetch(`${API_URL}/observations`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });
  return handleResponse<Observation>(res);
}

export async function deleteObservation(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/observations/${id}`, { 
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    if (res.status === 401) {
      setAuthToken(null);
      throw new Error('Требуется авторизация');
    }
    const detail = await res.text();
    throw new Error(detail || 'Не удалось удалить наблюдение');
  }
}

export async function requestComputation(): Promise<ComputeResponse> {
  const res = await fetch(`${API_URL}/compute`, { 
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse<ComputeResponse>(res);
}
