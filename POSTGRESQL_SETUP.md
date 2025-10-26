# ✅ Миграция на PostgreSQL завершена

## Что было сделано

### 📦 Изменённые файлы

1. **docker-compose.yml**
   - ✨ Добавлен сервис PostgreSQL 16 (`db`)
   - ✨ Добавлен volume `postgres_data` для хранения данных
   - ❌ Удален volume `./data` (SQLite больше не используется)
   - ✅ Backend зависит от здоровья БД (healthcheck)

2. **backend/requirements.txt**
   - ✨ Добавлен `psycopg2-binary==2.9.9` (PostgreSQL драйвер)

3. **backend/app/config.py**
   - ✏️ Изменен DATABASE_URL по умолчанию на PostgreSQL
   - ❌ Удален код создания директории для SQLite

4. **backend/app/database.py**
   - ❌ Удален параметр `check_same_thread` (специфичен для SQLite)
   - ✨ Добавлены параметры `echo=False, pool_pre_ping=True`

5. **.env** ✨ НОВЫЙ ФАЙЛ
   - Настройки подключения к PostgreSQL
   - Переменные окружения для локальной разработки

6. **.env.example**
   - ✏️ Обновлен с примерами для PostgreSQL
   - ✨ Добавлены комментарии для Docker и локальной разработки

7. **README.md**
   - ✏️ Обновлена документация
   - ✨ Добавлены инструкции по PostgreSQL
   - ✏️ Изменены команды очистки данных

8. **backend/migrate_sqlite_to_postgres.py** ✨ НОВЫЙ ФАЙЛ
   - Скрипт для миграции данных из SQLite в PostgreSQL
   - Автоматический перенос наблюдений и решений орбит

9. **MIGRATION.md** ✨ НОВЫЙ ФАЙЛ
   - Подробная инструкция по миграции
   - Troubleshooting
   - Полезные команды

## 🚀 Быстрый запуск

### Для новых пользователей (нет данных SQLite)

```bash
# Просто запустите Docker Compose
docker compose up --build
```

Готово! Приложение будет доступно на:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

### Для существующих пользователей (есть data/app.db)

```bash
# 1. Запустите PostgreSQL
docker compose up -d db

# 2. Дождитесь запуска БД (10 секунд)
timeout /t 10

# 3. Мигрируйте данные
cd backend
pip install -r requirements.txt
python migrate_sqlite_to_postgres.py

# 4. Запустите все сервисы
cd ..
docker compose up --build
```

## 📊 Структура БД PostgreSQL

**База данных:** `cometlab`  
**Пользователь:** `cometuser`  
**Пароль:** `cometpass123`

**Таблицы:**
- `observation` - наблюдения комет
- `orbitsolution` - рассчитанные орбиты

## 🔍 Проверка работы

1. Откройте Swagger UI: http://localhost:8000/docs
2. Попробуйте создать наблюдение через `/observations` POST
3. Проверьте список: `/observations` GET
4. Добавьте 5+ наблюдений и вызовите `/compute` POST

## 🛠️ Полезные команды

### Подключение к PostgreSQL

```bash
# Через Docker
docker exec -it comet-postgres psql -U cometuser -d cometlab

# Локально (если установлен psql)
psql -U cometuser -d cometlab -h localhost
```

### SQL команды

```sql
-- Посмотреть таблицы
\dt

-- Количество записей
SELECT COUNT(*) FROM observation;
SELECT COUNT(*) FROM orbitsolution;

-- Посмотреть данные
SELECT id, ra_hours, dec_degrees, observation_time FROM observation LIMIT 5;

-- Очистить данные
TRUNCATE observation, orbitsolution RESTART IDENTITY CASCADE;

-- Выход
\q
```

### Docker команды

```bash
# Остановить все сервисы
docker compose down

# Остановить и удалить volumes (УДАЛИТ ДАННЫЕ!)
docker compose down -v

# Посмотреть логи
docker compose logs -f

# Посмотреть логи только БД
docker compose logs -f db

# Перезапустить сервис
docker compose restart backend
```

## 📁 Структура хранения данных

**До миграции (SQLite):**
```
├── data/
│   └── app.db          # Файл базы данных
└── uploads/            # Фотографии
    └── *.jpg, *.png
```

**После миграции (PostgreSQL):**
```
├── postgres_data/      # Docker volume (внутри Docker)
└── uploads/            # Фотографии (без изменений)
    └── *.jpg, *.png
```

**⚠️ Важно:** Фотографии в `uploads/` остаются на месте и не требуют миграции!

## ✅ Преимущества PostgreSQL

1. **Производительность** - быстрее при множественных запросах
2. **Масштабируемость** - поддержка большого количества пользователей
3. **Надёжность** - ACID транзакции, репликация
4. **Production-ready** - стандарт для промышленных приложений
5. **Расширенные возможности** - JSON, полнотекстовый поиск, геоданные

## 🔄 Откат на SQLite (при необходимости)

Если вам нужно вернуться к SQLite:

```bash
# Восстановите старые файлы
git checkout HEAD -- docker-compose.yml backend/requirements.txt backend/app/config.py backend/app/database.py

# Обновите .env
echo "DATABASE_URL=sqlite:///data/app.db" > .env

# Перезапустите
docker compose down
docker compose up --build
```

## 📞 Получение помощи

Если возникли проблемы:

1. Проверьте `MIGRATION.md` - раздел Troubleshooting
2. Посмотрите логи: `docker compose logs`
3. Проверьте статус: `docker compose ps`
4. Проверьте .env файл на корректность

## 🎉 Готово!

Ваш проект теперь использует PostgreSQL и готов к production-деплою!

**Следующие шаги:**
- Протестируйте добавление наблюдений
- Проверьте расчет орбит (минимум 5 наблюдений)
- Попробуйте подключиться к БД через pgAdmin или DBeaver
- Настройте бэкапы PostgreSQL для production

---

**Учётные данные PostgreSQL:**
- Database: `cometlab`
- User: `cometuser`
- Password: `cometpass123`
- Host: `localhost` (или `db` внутри Docker)
- Port: `5432`
