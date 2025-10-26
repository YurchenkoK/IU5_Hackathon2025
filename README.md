# 🌠 Кометное бюро - Comet Observation System

Приложение для отслеживания комет и расчета их орбит. Вдохновлено фильмом "Don't Look Up".

## 📋 Возможности

- ✅ Добавление наблюдений (RA, Dec, время, фото)
- ✅ Загрузка и хранение фотографий наблюдений
- ✅ Расчет орбитальных элементов кометы (a, e, i, Ω, ω, T_peri)
- ✅ Определение точки максимального сближения с Землей
- ✅ Расчет расстояния и относительной скорости

## 🛠 Технологический стек

### Frontend
- React 19
- TypeScript
- Vite
- CSS

### Backend
- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Astropy (астрономические расчеты)
- Poliastro (орбитальная механика)

### DevOps
- Docker & Docker Compose
- Nginx

## 📂 Структура проекта

```
IU5_Hackaton_New/
├── frontend/           # React приложение
│   ├── src/
│   │   ├── App.tsx    # Главный компонент
│   │   ├── api.ts     # API клиент
│   │   └── types.ts   # TypeScript типы
│   └── Dockerfile
├── backend/            # FastAPI бэкенд
│   ├── app/
│   │   ├── main.py         # API эндпоинты
│   │   ├── models.py       # БД модели
│   │   ├── schemas.py      # Pydantic схемы
│   │   ├── database.py     # Подключение к БД
│   │   ├── crud.py         # CRUD операции
│   │   ├── orbit_calc.py   # Астрономические расчеты
│   │   └── config.py       # Конфигурация
│   ├── uploads/        # Загруженные фото
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── .env
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker Desktop
- Docker Compose

### Запуск приложения

1. **Клонировать репозиторий и перейти в директорию:**
```powershell
cd "C:\Users\fenix\Downloads\Telegram Desktop\IU5_Hackaton_New"
```

2. **Запустить Docker Compose:**
```powershell
docker-compose up --build
```

3. **Открыть в браузере:**
- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Остановка приложения

```powershell
docker-compose down
```

### Полная очистка (включая данные БД)

```powershell
docker-compose down -v
```

## 📡 API Endpoints

### Observations

- `GET /observations` - Получить все наблюдения
- `POST /observations` - Добавить наблюдение (FormData)
  - `ra_hours`: float (0-24)
  - `dec_degrees`: float (-90 to 90)
  - `observation_time`: ISO datetime string
  - `photo`: File (image)
- `DELETE /observations/{id}` - Удалить наблюдение

### Orbit Computation

- `POST /compute` - Рассчитать орбиту (требуется ≥5 наблюдений)

## 🔬 Астрономические расчеты

### Входные данные
- **RA (Right Ascension)**: Прямое восхождение в часах (0-24)
- **Dec (Declination)**: Склонение в градусах (-90 to 90)
- **Time**: Время наблюдения (UTC)

### Выходные данные

**Орбитальные элементы:**
- `a` - Большая полуось (а.е.)
- `e` - Эксцентриситет
- `i` - Наклонение (°)
- `Ω` - Долгота восходящего узла (°)
- `ω` - Аргумент перицентра (°)
- `T_peri` - Время прохождения перигелия

**Сближение с Землей:**
- Дата и время максимального сближения
- Расстояние (км)
- Относительная скорость (км/с)

## 🧪 Тестирование

### Ручное тестирование API

1. **Добавить наблюдение:**
```powershell
$boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
$body = @"
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="ra_hours"

12.5
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="dec_degrees"

-15.3
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="observation_time"

2025-10-26T12:00:00Z
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="photo"; filename="test.jpg"
Content-Type: image/jpeg

<binary data>
------WebKitFormBoundary7MA4YWxkTrZu0gW--
"@

Invoke-WebRequest -Uri "http://localhost:8000/observations" -Method POST -ContentType "multipart/form-data; boundary=$boundary" -Body $body
```

2. **Получить наблюдения:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/observations" | ConvertFrom-Json
```

3. **Рассчитать орбиту (после добавления 5+ наблюдений):**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/compute" -Method POST | ConvertFrom-Json
```

## 🎯 Особенности реализации

### Упрощенный метод Гаусса
Для определения орбиты используется упрощенная версия метода Гаусса. В production-версии необходимо:
- Реализовать полный метод Гаусса для orbit determination
- Добавить метод наименьших квадратов для использования всех наблюдений
- Улучшить обработку ошибок и edge cases

### База данных
- Асинхронная работа с PostgreSQL через asyncpg
- Автоматическое создание таблиц при запуске
- Хранение метаданных наблюдений

### Файловое хранилище
- Уникальные имена файлов (UUID)
- Валидация типов и размеров файлов
- Максимальный размер: 10 MB

## 🐛 Известные проблемы и TODO

- [ ] Реализовать полный метод Гаусса
- [ ] Добавить метод наименьших квадратов для всех наблюдений
- [ ] Улучшить UI/UX
- [ ] Добавить визуализацию орбиты
- [ ] Добавить экспорт результатов
- [ ] Реализовать пагинацию для наблюдений
- [ ] Добавить unit тесты

## 📝 Лицензия

MIT

## 👥 Авторы

Hackathon IU5 Team

---

**Don't Look Up!** 🌠☄️
