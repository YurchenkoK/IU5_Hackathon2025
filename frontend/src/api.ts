import type { ComputeResponse, Observation } from './types';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

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
  const res = await fetch(`${API_URL}/observations`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<Observation>(res);
}

export async function deleteObservation(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/observations/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Не удалось удалить наблюдение');
  }
}

export async function requestComputation(): Promise<ComputeResponse> {
  const res = await fetch(`${API_URL}/compute`, { method: 'POST' });
  return handleResponse<ComputeResponse>(res);
}
