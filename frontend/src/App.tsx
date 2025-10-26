import type { FormEvent } from 'react';
import { useEffect, useMemo, useState } from 'react';

import {
  API_URL,
  deleteObservation,
  fetchObservations,
  requestComputation,
  submitObservation,
  login,
  register,
  logout,
  getCurrentUser,
  getToken,
  type UserResponse,
} from './api';
import type { ComputeResponse, Observation } from './types';

type FormState = {
  ra: string;
  dec: string;
  time: string;
  photo: File | null;
};

const INITIAL_FORM: FormState = { ra: '', dec: '', time: '', photo: null };

const parseCoordinate = (value: string, mode: 'ra' | 'dec'): number | null => {
  if (!value.trim()) {
    return null;
  }

  const trimmed = value.trim();
  const sign = mode === 'dec' && trimmed.startsWith('-') ? -1 : 1;
  const cleaned = trimmed.replace(/^[+-]/, '');
  const fragments = cleaned.split(/[:\s]+/).filter(Boolean);
  const numbers = fragments.map((part) => Number(part));

  if (numbers.some((num) => Number.isNaN(num))) {
    return null;
  }

  const [major, minor = 0, seconds = 0] = numbers;
  const decimal = major + minor / 60 + seconds / 3600;

  if (mode === 'ra') {
    if (decimal < 0 || decimal >= 24) {
      return null;
    }
    return decimal;
  }

  const decValue = sign * decimal;
  if (decValue < -90 || decValue > 90) {
    return null;
  }
  return decValue;
};

const formatNumber = (value: number, digits = 3) => (Number.isFinite(value) ? value.toFixed(digits) : '—');

const toIsoString = (value: string) => {
  const date = new Date(value);
  if (!Number.isNaN(date.getTime())) {
    return date.toISOString();
  }

  const match = value.trim().match(/^(\d{2})[.\-/](\d{2})[.\-/](\d{4})\s+(\d{2}):(\d{2})$/);
  if (!match) {
    return null;
  }
  const [, dd, mm, yyyy, hh, min] = match;
  const fallback = new Date(Number(yyyy), Number(mm) - 1, Number(dd), Number(hh), Number(min));
  if (Number.isNaN(fallback.getTime())) {
    return null;
  }
  return fallback.toISOString();
};

const thumbnailUrl = (path: string) => {
  if (!path) {
    return '';
  }
  if (path.startsWith('http')) {
    return path;
  }
  return `${API_URL}${path}`;
};

function App() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [results, setResults] = useState<ComputeResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Auth state
  const [user, setUser] = useState<UserResponse | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '' });

  useEffect(() => {
    loadObservations();
    checkAuth();
  }, []);

  async function checkAuth() {
    if (getToken()) {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (err) {
        logout();
        setUser(null);
      }
    }
  }

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login({ username: authForm.username, password: authForm.password });
      const userData = await getCurrentUser();
      setUser(userData);
      setSuccess('Вход выполнен!');
      setAuthForm({ username: '', email: '', password: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка входа');
    }
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await register({ 
        username: authForm.username, 
        email: authForm.email, 
        password: authForm.password 
      });
      await login({ username: authForm.username, password: authForm.password });
      const userData = await getCurrentUser();
      setUser(userData);
      setSuccess('Регистрация успешна!');
      setAuthForm({ username: '', email: '', password: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка регистрации');
    }
  }

  async function handleLogout() {
    logout();
    setUser(null);
    setSuccess('Вы вышли из системы');
  }

  useEffect(() => {
    loadObservations();
  }, []);

  async function loadObservations() {
    try {
      const data = await fetchObservations();
      setObservations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось получить наблюдения.');
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const ra = parseCoordinate(form.ra, 'ra');
    const dec = parseCoordinate(form.dec, 'dec');
    const isoTime = toIsoString(form.time);

    if (ra === null || dec === null || !isoTime || !form.photo) {
      setError('Нужны валидные координаты (0≤RA<24, -90≤Dec≤90), дата/время и кадр.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = new FormData();
      payload.append('ra_hours', ra.toString());
      payload.append('dec_degrees', dec.toString());
      payload.append('observation_time', isoTime);
      payload.append('photo', form.photo);

      const created = await submitObservation(payload);
      setObservations((prev) => [...prev, created]);
      setForm(INITIAL_FORM);
      setSuccess('Наблюдение сохранено!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при добавлении наблюдения.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompute = async () => {
    setError(null);
    setSuccess(null);
    setComputing(true);
    try {
      const response = await requestComputation();
      setResults(response);
      setSuccess('Орбита успешно посчитана.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось рассчитать орбиту.');
    } finally {
      setComputing(false);
    }
  };

  const handleDelete = async (id: number) => {
    setError(null);
    setSuccess(null);
    try {
      await deleteObservation(id);
      setObservations((prev) => prev.filter((obs) => obs.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить наблюдение.');
    }
  };

  const formattedObservations = useMemo(
    () =>
      observations
        .slice()
        .sort((a, b) => new Date(a.observation_time).getTime() - new Date(b.observation_time).getTime())
        .map((obs) => ({
          ...obs,
          localTime: new Date(obs.observation_time).toLocaleString(),
        })),
    [observations],
  );

  const enoughObservations = formattedObservations.length >= 5;
  const orbit = results?.orbit;
  const closestApproach = results?.closest_approach;

  // If not logged in, show auth form
  if (!user) {
    return (
      <>
        <header className="page-header">
          <h1>Кометное бюро</h1>
          <p>Войдите или зарегистрируйтесь для работы с наблюдениями</p>
        </header>

        <div className="grid" style={{ maxWidth: '500px', margin: '0 auto' }}>
          <section className="panel">
            <h2>{authMode === 'login' ? 'Вход' : 'Регистрация'}</h2>
            
            {error && <div className="message error">{error}</div>}
            {success && <div className="message success">{success}</div>}
            
            <form onSubmit={authMode === 'login' ? handleLogin : handleRegister}>
              <div>
                <label htmlFor="username">Имя пользователя</label>
                <input
                  id="username"
                  value={authForm.username}
                  onChange={(e) => setAuthForm(prev => ({ ...prev, username: e.target.value }))}
                  required
                />
              </div>
              
              {authMode === 'register' && (
                <div>
                  <label htmlFor="email">Email</label>
                  <input
                    id="email"
                    type="email"
                    value={authForm.email}
                    onChange={(e) => setAuthForm(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
              )}
              
              <div>
                <label htmlFor="password">Пароль</label>
                <input
                  id="password"
                  type="password"
                  value={authForm.password}
                  onChange={(e) => setAuthForm(prev => ({ ...prev, password: e.target.value }))}
                  required
                />
              </div>
              
              <button type="submit">
                {authMode === 'login' ? 'Войти' : 'Зарегистрироваться'}
              </button>
            </form>
            
            <p style={{ textAlign: 'center', marginTop: '1rem' }}>
              {authMode === 'login' ? (
                <>
                  Нет аккаунта?{' '}
                  <button 
                    type="button" 
                    onClick={() => setAuthMode('register')}
                    style={{ background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', textDecoration: 'underline' }}
                  >
                    Зарегистрироваться
                  </button>
                </>
              ) : (
                <>
                  Уже есть аккаунт?{' '}
                  <button 
                    type="button" 
                    onClick={() => setAuthMode('login')}
                    style={{ background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', textDecoration: 'underline' }}
                  >
                    Войти
                  </button>
                </>
              )}
            </p>
          </section>
        </div>
      </>
    );
  }

  return (
    <>
      <header className="page-header">
        <p>Лаборатория вдохновлена Don't Look Up.</p>
        <h1>Кометное бюро</h1>
        <p>Добавьте минимум 5 наблюдений, чтобы получить приближенную орбиту и точку максимального сближения.</p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Пользователь: <strong>{user.username}</strong></span>
          <button 
            onClick={handleLogout}
            style={{ 
              padding: '4px 10px', 
              cursor: 'pointer',
              fontSize: '0.75rem',
              backgroundColor: '#4a5568',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontWeight: '500'
            }}
          >
            Выйти
          </button>
        </div>
      </header>

      <div className="grid">
        <section className="panel">
          <h2>Добавить наблюдение</h2>
          <form onSubmit={handleSubmit}>
            <div>
              <label htmlFor="ra">Прямое восхождение (ч или ч:м:с)</label>
              <input
                id="ra"
                name="ra"
                placeholder="12 34 56.7"
                value={form.ra}
                onChange={(e) => setForm((prev) => ({ ...prev, ra: e.target.value }))}
                required
              />
            </div>
            <div>
              <label htmlFor="dec">Склонение (° или °:′:″)</label>
              <input
                id="dec"
                name="dec"
                placeholder="-01 23 45.6"
                value={form.dec}
                onChange={(e) => setForm((prev) => ({ ...prev, dec: e.target.value }))}
                required
              />
            </div>
            <div>
              <label htmlFor="time">Время наблюдения (UTC)</label>
              <input
                id="time"
                name="time"
                type="datetime-local"
                value={form.time}
                onChange={(e) => setForm((prev) => ({ ...prev, time: e.target.value }))}
                required
              />
            </div>
            <div>
              <label htmlFor="photo">Фото кадра</label>
              <label 
                htmlFor="photo" 
                style={{
                  display: 'inline-block',
                  padding: '10px 20px',
                  backgroundColor: '#4a5568',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  textAlign: 'center',
                  fontWeight: '500',
                  transition: 'background-color 0.2s',
                  border: '2px solid #4a5568'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2d3748'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#4a5568'}
              >
                📷 {form.photo ? form.photo.name : 'Выберите файл'}
              </label>
              <input
                id="photo"
                name="photo"
                type="file"
                accept="image/*"
                onChange={(e) => setForm((prev) => ({ ...prev, photo: e.target.files?.[0] ?? null }))}
                required
                style={{ display: 'none' }}
              />
            </div>
            <button type="submit" disabled={submitting}>
              {submitting ? 'Сохраняем…' : 'Сохранить наблюдение'}
            </button>
          </form>
        </section>

        <section className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>Наблюдения</h2>
            <span>{formattedObservations.length} / 5</span>
          </div>

          <div className="observations">
            {formattedObservations.length === 0 && <p style={{ color: '#97a3d6' }}>Пока нет записей.</p>}
            {formattedObservations.map((obs) => (
              <article className="observation-card" key={obs.id}>
                <img src={thumbnailUrl(obs.photo_url)} alt="Observation" />
                <div className="observation-meta">
                  <strong>RA {formatNumber(obs.ra_hours, 2)} ч</strong> ·{' '}
                  <strong>Dec {formatNumber(obs.dec_degrees, 2)}°</strong>
                  <div>{obs.localTime}</div>
                </div>
                <button className="ghost-button" type="button" onClick={() => handleDelete(obs.id)}>
                  Удалить
                </button>
              </article>
            ))}
          </div>

          <button type="button" onClick={handleCompute} disabled={!enoughObservations || computing} style={{ marginTop: '1.5rem' }}>
            {computing ? 'Считаем…' : 'Рассчитать орбиту'}
          </button>
        </section>
      </div>

      {results && (
        <section className="panel" style={{ marginTop: '1.5rem' }}>
          <h2>Результаты вычислений орбиты</h2>
          <div className="results">
            <div className="result-card">
              <h4>A (А.Е.)</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Большая полуось</p>
              <strong>{formatNumber(orbit!.semi_major_axis_au)}</strong>
            </div>
            <div className="result-card">
              <h4>E</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Эксцентриситет</p>
              <strong>{formatNumber(orbit!.eccentricity)}</strong>
            </div>
            <div className="result-card">
              <h4>I (°)</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Наклонение</p>
              <strong>{formatNumber(orbit!.inclination_deg)}</strong>
            </div>
            <div className="result-card">
              <h4>Ω (°)</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Долгота узла</p>
              <strong>{formatNumber(orbit!.raan_deg)}</strong>
            </div>
            <div className="result-card">
              <h4>ω (°)</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Аргумент перигелия</p>
              <strong>{formatNumber(orbit!.arg_periapsis_deg)}</strong>
            </div>
            <div className="result-card">
              <h4>T<sub>PERI</sub></h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Время перигелия</p>
              <strong>{new Date(orbit!.perihelion_time).toLocaleString()}</strong>
            </div>
            <div className="result-card">
              <h4>D<sub>MIN</sub> (KM)</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Расстояние до Земли</p>
              <strong>{formatNumber((closestApproach!.distance_km ?? 0) / 1000, 2)}k</strong>
            </div>
            <div className="result-card">
              <h4>КОГДА</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Дата сближения</p>
              <strong>{new Date(closestApproach!.approach_datetime).toLocaleString()}</strong>
            </div>
            <div className="result-card">
              <h4>СКОРОСТЬ (КМ/С)</h4>
              <p style={{ fontSize: '0.75rem', margin: '0.25rem 0', opacity: 0.7 }}>Относительная скорость</p>
              <strong>{formatNumber(closestApproach!.relative_speed_kms)}</strong>
            </div>
          </div>
        </section>
      )}

      {error && (
        <div className="status error" role="alert">
          {error}
        </div>
      )}
      {success && <div className="status success">{success}</div>}
    </>
  );
}

export default App;
