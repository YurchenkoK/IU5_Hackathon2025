# Don’t Look Up — Comet Lab

Учебный pet‑проект «лаборатории комет» из Don’t Look Up. Пользователь добавляет минимум пять наблюдений (RA/Dec, время, фотография), а backend на FastAPI + `poliastro`/`astropy` оценивает орбиту и ближайшее сближение с Землёй. Приложение снова умеет работать в Docker-контейнерах и хранит данные в SQLite через SQLModel.

## Стек
- **Backend:** FastAPI, SQLModel (SQLite), `poliastro`, `astropy`.
- **Frontend:** React + Vite, статическая выдача через nginx в контейнере.
- **Инфраструктура:** Docker/Docker Compose для полного окружения, `uploads/` и `data/` примонтированы наружу.

## Требования локально
- Python 3.11+
- Node.js 20+ и npm
- Docker (если хотите контейнеры)

## Переменные окружения
Скопируйте `.env.example` → `.env`. Ключевые переменные:

```env
DATABASE_URL=sqlite:///data/app.db
UPLOAD_DIR=uploads
FRONTEND_ORIGIN=http://localhost:5173
SAMPLE_PROPAGATION_DAYS=365
VITE_API_URL=http://localhost:8000
```

Фронтенд читает `VITE_API_URL` во время сборки (`frontend/.env` можно оставить с тем же значением).

## Запуск через Docker Compose
```bash
docker compose up --build
```

- Backend станет доступен на `http://localhost:8000` (Swagger на `/docs`, статика фотографий — `/uploads/...`).  
- Frontend (nginx) откроется на `http://localhost:5173`.  
- Каталоги `./data` и `./uploads` примонтированы, поэтому база (`data/app.db`) и фотографии сохраняются вне контейнеров.

Остановить: `docker compose down`. Пересобрать после изменений: `docker compose up --build`.

## Ручной запуск без Docker
### Backend
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # Linux/macOS
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Полезное
- Минимум 5 наблюдений перед вызовом `/compute`, иначе получим 400.
- Валидный диапазон координат: `0 ≤ RA < 24` часов, `-90° ≤ Dec ≤ 90°`. Несоблюдение диапазона вызывает 400-ю ошибку.
- Для очистки данных остановите backend, удалите `data/app.db` и содержимое `uploads/`.
- Production-сборка фронтенда: `npm run build` (артефакты в `frontend/dist/`). Можно скопировать их в любой статический сервер.

## Пример наблюдений

| # | RA (ч) | Dec (°) | Время наблюдения (UTC) |
| - | ------ | ------- | ---------------------- |
| 1 | 12 44 10.5 | +05 12 33 | 2025-03-01 01:10 |
| 2 | 12 46 55.2 | +05 18 02 | 2025-03-02 00:58 |
| 3 | 12 49 31.0 | +05 23 40 | 2025-03-03 00:47 |
| 4 | 12 52 06.8 | +05 29 18 | 2025-03-04 00:36 |
| 5 | 12 54 42.7 | +05 34 57 | 2025-03-05 00:25 |

Достаточно внести эти значения, добавить любые изображения и сервис без ошибок рассчитает примерную орбиту. Если нужно обнулить всё и повторить эксперимент — воспользуйтесь кнопкой удаления рядом с каждой записью или удалите `data/app.db`.

Теперь проект снова готов к запуску в контейнерах; локальный режим никуда не делся, если удобнее отлаживаться без Docker.
