import type { FormEvent } from 'react';
import { useEffect, useMemo, useState } from 'react';
import styled from 'styled-components';

import {
  API_URL,
  deleteObservation,
  fetchObservations,
  requestComputation,
  submitObservation,
  login,
  setAuthToken,
  getAuthToken,
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

const FileUploadButton = styled.label`
  display: inline-flex;
  align-items: center;
  padding: 12px 24px;
  background: linear-gradient(135deg, #6e8efb 0%, #4a6cf7 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
    background: linear-gradient(135deg, #5d7df9 0%, #3955e6 100%);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  input[type='file'] {
    display: none;
  }
`;

type HistoryEntry = {
  id: number;
  timestamp: string;
  username: string;
  orbit: ComputeResponse['orbit'];
  closestApproach: ComputeResponse['closest_approach'];
};

// Список доступных пользователей
const USERS = [
  { username: 'client', password: 'password' },
  { username: 'observer1', password: 'pass123' },
  { username: 'observer2', password: 'pass456' },
  { username: 'observer3', password: 'pass789' },
];

function App() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [results, setResults] = useState<ComputeResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedInUser, setLoggedInUser] = useState<string | null>(getAuthToken() ? 'client' : null);
  const [computationHistory, setComputationHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (loggedInUser) {
      loadObservations();
    }
  }, [loggedInUser]);

  // Загружаем историю при монтировании компонента и смене пользователя
  useEffect(() => {
    if (loggedInUser) {
      const savedHistory = localStorage.getItem('computationHistory');
      if (savedHistory) {
        const allHistory = JSON.parse(savedHistory);
        // Фильтруем историю только для текущего пользователя
        const userHistory = allHistory.filter((entry: HistoryEntry) => entry.username === loggedInUser);
        setComputationHistory(userHistory);
      }
    }
  }, [loggedInUser]);

  const filteredHistory = useMemo(() => {
    return computationHistory.filter(entry => entry.username === loggedInUser);
  }, [computationHistory, loggedInUser]);

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
      // Добавляем результат в историю
      const historyEntry: HistoryEntry = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        username: loggedInUser!,
        orbit: response.orbit,
        closestApproach: response.closest_approach,
      };
      setComputationHistory((prev) => [historyEntry, ...prev]);
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      // Проверяем учетные данные из списка пользователей
      const user = USERS.find(u => u.username === username && u.password === password);
      if (!user) {
        throw new Error('Неверные учетные данные');
      }

      const resp = await login(username, password);
      setAuthToken(resp.access_token);
      setLoggedInUser(username);
      setSuccess('Вошли как ' + username);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось войти');
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    setLoggedInUser(null);
    setSuccess('Вышли');
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

  // Показываем экран входа первым, пока нет токена
  if (!loggedInUser) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <div style={{ width: 420, background: 'var(--panel-bg, #071026)', padding: '2rem', borderRadius: 12, boxShadow: '0 6px 30px rgba(0,0,0,0.6)' }}>
          <h2 style={{ marginTop: 0 }}>Вход</h2>
          <form onSubmit={handleLogin} style={{ display: 'grid', gap: '0.75rem' }}>
            <input placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input placeholder="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button type="submit" style={{ padding: '0.6rem 1rem' }}>Войти</button>
            </div>
          </form>
          {error && <div style={{ marginTop: '0.75rem', color: '#ff8080' }}>{error}</div>}
          <div style={{ marginTop: '1rem', color: '#97a3d6', fontSize: 12 }}>
            Используйте default: <strong>client</strong> / <strong>password</strong>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
          <div>
            <p>Лаборатория вдохновлена Don't Look Up.</p>
            <h1>Кометное бюро</h1>
            <p>Добавьте минимум 5 наблюдений, чтобы получить приближенную орбиту и точку максимального сближения.</p>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              type="button"
              className="ghost-button"
              onClick={() => setShowHistory(!showHistory)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              {showHistory ? '🔽 Скрыть историю' : '🔼 Показать историю'}
              {computationHistory.length > 0 &&
                <span style={{
                  background: '#4a6cf7',
                  color: 'white',
                  borderRadius: '999px',
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.75rem'
                }}>
                  {computationHistory.length}
                </span>
              }
            </button>
            <button type="button" className="ghost-button" onClick={handleLogout}>
              Выйти
            </button>
          </div>
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
              {/* Заменяем старую кнопку на новую стилизованную */}
              <FileUploadButton>
                <input
                  type="file"
                  onChange={(e) => setForm((prev) => ({ ...prev, photo: e.target.files?.[0] ?? null }))}
                  accept="image/*"
                />
                Выберите фото наблюдения
              </FileUploadButton>
            </div>
            <button type="submit" disabled={submitting}>
              {submitting ? 'Сохраняем…' : 'Сохранить наблюдение'}
            </button>
          </form>
        </section>

        <section className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>Наблюдения</h2>
            <span>{formattedObservations.length} наблюдений</span>
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
          <h2>Результаты</h2>
          <div className="results">
            <div className="result-card">
              <h4>a (а.е.)</h4>
              <strong>{formatNumber(orbit!.semi_major_axis_au)}</strong>
            </div>
            <div className="result-card">
              <h4>e</h4>
              <strong>{formatNumber(orbit!.eccentricity)}</strong>
            </div>
            <div className="result-card">
              <h4>i (°)</h4>
              <strong>{formatNumber(orbit!.inclination_deg)}</strong>
            </div>
            <div className="result-card">
              <h4>Ω (°)</h4>
              <strong>{formatNumber(orbit!.raan_deg)}</strong>
            </div>
            <div className="result-card">
              <h4>ω (°)</h4>
              <strong>{formatNumber(orbit!.arg_periapsis_deg)}</strong>
            </div>
            <div className="result-card">
              <h4>T<sub>peri</sub></h4>
              <strong>{new Date(orbit!.perihelion_time).toLocaleString()}</strong>
            </div>
            <div className="result-card">
              <h4>d<sub>min</sub> (км)</h4>
              <strong>{formatNumber((closestApproach!.distance_km ?? 0) / 1000, 2)}k</strong>
            </div>
            <div className="result-card">
              <h4>Когда</h4>
              <strong>{new Date(closestApproach!.datetime).toLocaleString()}</strong>
            </div>
            <div className="result-card">
              <h4>Скорость (км/с)</h4>
              <strong>{formatNumber(closestApproach!.relative_speed_kms)}</strong>
            </div>
          </div>
        </section>
      )}

      {showHistory && (
        <section className="panel" style={{ marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>История вычислений для {loggedInUser}</h2>
            <span>{filteredHistory.length} вычислений</span>
          </div>
          <div className="computation-history">
            {filteredHistory.length === 0 ? (
              <p style={{ color: '#97a3d6' }}>История пуста</p>
            ) : (
              filteredHistory.map((entry) => (
                <article key={entry.id} className="history-entry" style={{
                  padding: '1rem',
                  marginBottom: '1rem',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '8px',
                  transition: 'all 0.3s ease'
                }}>
                  <div style={{ marginBottom: '0.5rem', color: '#97a3d6' }}>
                    {new Date(entry.timestamp).toLocaleString()}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    <div>
                      <h4>Орбитальные элементы</h4>
                      <div>a = {formatNumber(entry.orbit.semi_major_axis_au)} а.е.</div>
                      <div>e = {formatNumber(entry.orbit.eccentricity)}</div>
                      <div>i = {formatNumber(entry.orbit.inclination_deg)}°</div>
                    </div>
                    <div>
                      <h4>Сближение</h4>
                      <div>Расстояние: {formatNumber((entry.closestApproach.distance_km ?? 0) / 1000, 2)}k км</div>
                      <div>Дата: {new Date(entry.closestApproach.datetime).toLocaleString()}</div>
                      <div>Скорость: {formatNumber(entry.closestApproach.relative_speed_kms)} км/с</div>
                    </div>
                  </div>
                </article>
              ))
            )}
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
