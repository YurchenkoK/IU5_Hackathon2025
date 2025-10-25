import type { FormEvent } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { fetchObservations, requestComputation, submitObservation, API_URL } from './api';
import type { ComputeResponse, Observation } from './types';

type FormState = {
  ra: string;
  dec: string;
  time: string;
  photo?: File | null;
};

const getDefaultForm = (): FormState => ({
  ra: '',
  dec: '',
  time: '',
  photo: null,
});

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

  let decimal: number;
  if (numbers.length === 1) {
    decimal = numbers[0];
  } else {
    const [major, minor = 0, seconds = 0] = numbers;
    decimal = major + minor / 60 + seconds / 3600;
  }

  if (mode === 'ra') {
    return decimal;
  }
  return sign * decimal;
};

const formatNumber = (value: number, digits = 3) => value.toFixed(digits);

const toIsoString = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toISOString();
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
  const [form, setForm] = useState<FormState>(getDefaultForm());
  const [observations, setObservations] = useState<Observation[]>([]);
  const [results, setResults] = useState<ComputeResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

  const enoughObservations = observations.length >= 5;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const ra = parseCoordinate(form.ra, 'ra');
    const dec = parseCoordinate(form.dec, 'dec');
    const isoTime = toIsoString(form.time);
    if (ra === null || dec === null || !isoTime || !form.photo) {
      setError('Заполните координаты, время и приложите фото.');
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
      setForm(getDefaultForm());
      setSuccess('Наблюдение добавлено!');
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
      setSuccess('Орбита обновлена.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось рассчитать орбиту.');
    } finally {
      setComputing(false);
    }
  };

  const closestApproach = results?.closest_approach;
  const orbit = results?.orbit;

  const formattedObservations = useMemo(
    () =>
      observations.map((obs) => ({
        ...obs,
        localTime: new Date(obs.observation_time).toLocaleString(),
      })),
    [observations],
  );

  return (
    <>
      <header className="page-header">
        <p>Проект Don’t Look Up · трек «Комета»</p>
        <h1>Кометная лаборатория</h1>
        <p>Соберите минимум 5 наблюдений, чтобы оценить орбиту и прогноз сближения с Землей.</p>
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
              <input
                id="photo"
                name="photo"
                type="file"
                accept="image/*"
                onChange={(e) => setForm((prev) => ({ ...prev, photo: e.target.files?.[0] ?? null }))}
                required
              />
            </div>
            <button type="submit" disabled={submitting}>
              {submitting ? 'Загрузка...' : 'Сохранить наблюдение'}
            </button>
          </form>
        </section>

        <section className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>Наблюдения</h2>
            <span>{observations.length} / 5</span>
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
              </article>
            ))}
          </div>

          <button
            type="button"
            onClick={handleCompute}
            disabled={!enoughObservations || computing}
            style={{ marginTop: '1.5rem' }}
          >
            {computing ? 'Считаем...' : 'Рассчитать орбиту'}
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
              <h4>Мин. дистанция (км)</h4>
              <strong>{formatNumber(closestApproach!.distance_km / 1000, 2)}k</strong>
            </div>
            <div className="result-card">
              <h4>Дата сближения</h4>
              <strong>{new Date(closestApproach!.datetime).toLocaleString()}</strong>
            </div>
            <div className="result-card">
              <h4>Скорость (км/с)</h4>
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
      {success && (
        <div className="status success">
          {success}
        </div>
      )}
    </>
  );
}

export default App;
