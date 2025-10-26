# Don’t Look Up — Comet Lab

Учебный pet‑проект «лаборатории комет» из Don't Look Up. Пользователь добавляет минимум пять наблюдений (RA/Dec, время, фотография), а backend на FastAPI + `poliastro`/`astropy` оценивает орбиту и ближайшее сближение с Землёй. Приложение работает в Docker-контейнерах и хранит данные в PostgreSQL через SQLModel.

## Стек
- **Backend:** FastAPI, SQLModel (PostgreSQL), `poliastro`, `astropy`.
- **Frontend:** React + Vite, статическая выдача через nginx в контейнере.
- **База данных:** PostgreSQL 16
- **Инфраструктура:** Docker/Docker Compose для полного окружения, `uploads/` примонтирован наружу.

## Требования локально
- Python 3.11+
- Node.js 20+ и npm
- Docker (если хотите контейнеры)
- PostgreSQL 14+ (для локального запуска без Docker)

## Переменные окружения
Скопируйте `.env.example` → `.env`. Ключевые переменные:

```env
DATABASE_URL=postgresql://cometuser:cometpass123@localhost:5432/cometlab
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
- PostgreSQL доступен на `localhost:5432`
- Данные PostgreSQL сохраняются в Docker volume `postgres_data`
- Каталог `./uploads` примонтирован, поэтому фотографии сохраняются вне контейнеров.

Остановить: `docker compose down`. Пересобрать после изменений: `docker compose up --build`.

## Ручной запуск без Docker
### Настройка PostgreSQL
Создайте базу данных и пользователя:
```sql
CREATE DATABASE cometlab;
CREATE USER cometuser WITH PASSWORD 'cometpass123';
GRANT ALL PRIVILEGES ON DATABASE cometlab TO cometuser;
```

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
- Для очистки данных используйте endpoint `/reset` или подключитесь к PostgreSQL напрямую.
- Production-сборка фронтенда: `npm run build` (артефакты в `frontend/dist/`). Можно скопировать их в любой статический сервер.

## Пример наблюдений

| # | RA (ч) | Dec (°) | Время наблюдения (UTC) |
| - | ------ | ------- | ---------------------- |
| 1 | 12 44 10.5 | +05 12 33 | 2025-03-01 01:10 |
| 2 | 12 46 55.2 | +05 18 02 | 2025-03-02 00:58 |
| 3 | 12 49 31.0 | +05 23 40 | 2025-03-03 00:47 |
| 4 | 12 52 06.8 | +05 29 18 | 2025-03-04 00:36 |
| 5 | 12 54 42.7 | +05 34 57 | 2025-03-05 00:25 |

Достаточно внести эти значения, добавить любые изображения и сервис без ошибок рассчитает примерную орбиту. Если нужно обнулить всё и повторить эксперимент — воспользуйтесь кнопкой удаления рядом с каждой записью или вызовите `/reset` endpoint.

Теперь проект готов к запуску в контейнерах с PostgreSQL; локальный режим также поддерживается при наличии установленного PostgreSQL.
