# Миграция с SQLite на PostgreSQL

## Что изменилось

### 1. Docker Compose
- Добавлен сервис `db` с PostgreSQL 16
- Удален volume для SQLite (`data/`)
- Добавлен volume для PostgreSQL (`postgres_data`)
- Backend зависит от здоровья БД (healthcheck)

### 2. Backend Dependencies
- Добавлен `psycopg2-binary==2.9.9` в `requirements.txt`

### 3. Конфигурация
- `config.py`: изменен default DATABASE_URL на PostgreSQL
- `database.py`: убран SQLite-специфичный параметр `check_same_thread`
- Добавлен `.env` с настройками PostgreSQL
- Обновлен `.env.example`

### 4. README
- Обновлена документация с инструкциями по PostgreSQL
- Добавлены шаги для локального запуска с PostgreSQL

## Быстрый старт

### Вариант 1: Чистая установка с Docker

```bash
# Запустите контейнеры
docker compose up --build
```

Всё готово! PostgreSQL автоматически создаст базу и таблицы.

### Вариант 2: Миграция существующих данных из SQLite

Если у вас есть файл `data/app.db` с данными:

```bash
# 1. Запустите PostgreSQL
docker compose up -d db

# 2. Подождите пока БД запустится (10-15 секунд)

# 3. Установите зависимости (если еще не установлены)
cd backend
pip install -r requirements.txt

# 4. Запустите скрипт миграции
python migrate_sqlite_to_postgres.py

# 5. Запустите все сервисы
cd ..
docker compose up --build
```

### Вариант 3: Локальная разработка без Docker

```bash
# 1. Установите PostgreSQL
# https://www.postgresql.org/download/

# 2. Создайте БД и пользователя
psql -U postgres
```

```sql
CREATE DATABASE cometlab;
CREATE USER cometuser WITH PASSWORD 'cometpass123';
GRANT ALL PRIVILEGES ON DATABASE cometlab TO cometuser;
\q
```

```bash
# 3. Настройте .env
cp .env.example .env
# Убедитесь что DATABASE_URL=postgresql://cometuser:cometpass123@localhost:5432/cometlab

# 4. Запустите backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 5. В другом терминале запустите frontend
cd frontend
npm install
npm run dev
```

## Проверка миграции

1. Откройте http://localhost:8000/docs
2. Попробуйте создать наблюдение через Swagger UI
3. Проверьте список наблюдений

## Подключение к PostgreSQL

```bash
# Через Docker
docker exec -it comet-postgres psql -U cometuser -d cometlab

# Локально
psql -U cometuser -d cometlab -h localhost
```

### Полезные SQL команды

```sql
-- Посмотреть все таблицы
\dt

-- Посмотреть наблюдения
SELECT * FROM observation;

-- Посмотреть решения орбит
SELECT * FROM orbitsolution;

-- Количество записей
SELECT COUNT(*) FROM observation;
SELECT COUNT(*) FROM orbitsolution;

-- Очистить данные
TRUNCATE observation, orbitsolution RESTART IDENTITY CASCADE;
```

## Откат на SQLite (если нужно)

1. Восстановите старые версии файлов из git:
```bash
git checkout HEAD -- docker-compose.yml backend/requirements.txt backend/app/config.py backend/app/database.py
```

2. Обновите `.env`:
```bash
DATABASE_URL=sqlite:///data/app.db
```

3. Перезапустите:
```bash
docker compose down
docker compose up --build
```

## Преимущества PostgreSQL

✅ Лучшая производительность при многих пользователях  
✅ Поддержка транзакций и concurrent writes  
✅ Полноценная СУБД с репликацией и бэкапами  
✅ Стандарт для production-окружений  
✅ Расширенные типы данных и индексы  

## Структура проекта после миграции

```
IU5_Hackaton/
├── docker-compose.yml         # ✏️ Добавлен PostgreSQL сервис
├── .env                       # ✨ Новый файл с настройками PostgreSQL
├── .env.example              # ✏️ Обновлен для PostgreSQL
├── README.md                 # ✏️ Обновлена документация
├── MIGRATION.md              # ✨ Этот файл
├── backend/
│   ├── requirements.txt      # ✏️ Добавлен psycopg2-binary
│   ├── migrate_sqlite_to_postgres.py  # ✨ Скрипт миграции
│   └── app/
│       ├── config.py         # ✏️ PostgreSQL по умолчанию
│       └── database.py       # ✏️ Убран SQLite код
└── uploads/                  # ✅ Без изменений
```

## Troubleshooting

### Ошибка подключения к БД

**Проблема:** `could not connect to server`

**Решение:**
```bash
# Проверьте что PostgreSQL запущен
docker compose ps

# Посмотрите логи
docker compose logs db

# Перезапустите БД
docker compose restart db
```

### Ошибка "relation does not exist"

**Проблема:** Таблицы не созданы

**Решение:**
```bash
# Пересоздайте БД через backend
docker compose exec backend python -c "from app.database import init_db; init_db()"
```

### Порт 5432 уже занят

**Проблема:** У вас уже запущен локальный PostgreSQL

**Решение:**
```bash
# Измените порт в docker-compose.yml
ports:
  - "5433:5432"  # Используйте 5433 вместо 5432

# И обновите DATABASE_URL в docker-compose.yml (внутри контейнера остается :5432)
```

### Миграция не переносит все данные

**Проблема:** Скрипт миграции завершается с ошибкой

**Решение:**
```bash
# Проверьте что PostgreSQL доступен
docker compose exec db pg_isready -U cometuser

# Проверьте .env
cat .env | grep DATABASE_URL

# Попробуйте миграцию с подробными логами
python migrate_sqlite_to_postgres.py 2>&1 | tee migration.log
```
