# Аутентификация в Comet Lab

## Обзор

Приложение теперь защищено JWT-аутентификацией. Все основные endpoints требуют авторизации.

## Пользователи по умолчанию

При первом запуске автоматически создаются два пользователя:

| Username | Password | Описание |
|----------|----------|----------|
| `admin` | `admin` | Администратор (пока те же права) |
| `user` | `user` | Обычный пользователь |

⚠️ **Важно:** Измените пароли в production!

## API Endpoints

### Публичные (без авторизации)

#### `POST /login`
Аутентификация пользователя.

**Тело запроса** (form-data):
```
username: admin
password: admin
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### `POST /register`
Регистрация нового пользователя.

**Тело запроса** (JSON):
```json
{
  "username": "newuser",
  "password": "newpassword"
}
```

**Ответ:**
```json
{
  "id": 3,
  "username": "newuser",
  "created_at": "2025-10-26T12:00:00"
}
```

### Защищенные (требуют токен)

Все остальные endpoints требуют JWT токен в заголовке:
```
Authorization: Bearer <токен>
```

#### `GET /me`
Получить информацию о текущем пользователе.

#### `GET /observations`
Список всех наблюдений.

#### `POST /observations`
Создать новое наблюдение.

#### `DELETE /observations/{id}`
Удалить наблюдение.

#### `POST /compute`
Рассчитать орбиту (требует минимум 5 наблюдений).

#### `POST /reset`
Очистить все данные.

## Использование

### 1. Через Swagger UI (http://localhost:8000/docs)

1. Откройте `/docs`
2. Нажмите кнопку **"Authorize"** (замок) в правом верхнем углу
3. Войдите через форму:
   - Username: `admin`
   - Password: `admin`
4. Нажмите **"Login"**
5. Теперь можете использовать все endpoints

### 2. Через curl

```bash
# 1. Получите токен
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Ответ: {"access_token":"...","token_type":"bearer"}

# 2. Используйте токен в запросах
curl "http://localhost:8000/observations" \
  -H "Authorization: Bearer <ваш_токен>"
```

### 3. Через Python

```python
import requests

# Логин
response = requests.post(
    "http://localhost:8000/login",
    data={"username": "admin", "password": "admin"}
)
token = response.json()["access_token"]

# Используем токен
headers = {"Authorization": f"Bearer {token}"}

# Получаем наблюдения
observations = requests.get(
    "http://localhost:8000/observations",
    headers=headers
).json()

print(observations)
```

### 4. Через JavaScript/Fetch

```javascript
// Логин
const loginResponse = await fetch('http://localhost:8000/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: 'username=admin&password=admin'
});

const { access_token } = await loginResponse.json();

// Используем токен
const observationsResponse = await fetch('http://localhost:8000/observations', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const observations = await observationsResponse.json();
console.log(observations);
```

## Конфигурация

### JWT настройки (.env)

```env
# Секретный ключ для подписи токенов
# В production используйте: openssl rand -hex 32
SECRET_KEY=your-secret-key-change-in-production

# Алгоритм шифрования
ALGORITHM=HS256

# Время жизни токена (в минутах)
# 43200 = 30 дней
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

## Безопасность

### Для разработки
- ✅ Пароли хешируются с использованием bcrypt
- ✅ JWT токены подписываются секретным ключом
- ✅ Токены проверяются на каждом защищенном endpoint

### Для production

1. **Измените SECRET_KEY:**
   ```bash
   # Сгенерируйте безопасный ключ
   openssl rand -hex 32
   
   # Добавьте в .env
   SECRET_KEY=<ваш_новый_ключ>
   ```

2. **Измените пароли по умолчанию:**
   - Удалите пользователей admin/user из БД
   - Создайте новых через `/register`
   - Или измените хеши в БД

3. **Уменьшите время жизни токена:**
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 час
   ```

4. **Используйте HTTPS** для защиты токенов при передаче

## Структура БД

### Таблица `user`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | Primary key |
| `username` | String | Уникальное имя пользователя |
| `hashed_password` | String | Bcrypt хеш пароля |
| `created_at` | DateTime | Дата создания |

## Отладка

### Проверить содержимое токена

Зайдите на https://jwt.io и вставьте токен для декодирования.

Пример payload:
```json
{
  "sub": "admin",
  "exp": 1730034567
}
```

### Проверить пользователей в БД

```sql
-- Подключитесь к PostgreSQL
docker exec -it comet-postgres psql -U cometuser -d cometlab

-- Посмотрите пользователей
SELECT id, username, created_at FROM "user";
```

## FAQ

**Q: Что делать если забыл пароль?**
A: Подключитесь к БД и удалите пользователя, затем зарегистрируйтесь заново.

**Q: Токен истек, что делать?**
A: Войдите снова через `/login` для получения нового токена.

**Q: Можно ли отключить аутентификацию?**
A: Да, удалите `current_user: User = Depends(get_current_user)` из endpoints в `main.py`.

**Q: Как добавить роли (admin/user)?**
A: Добавьте поле `role` в модель `User`, обновите схемы и добавьте проверку прав в endpoints.

## Примеры ошибок

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```
**Решение:** Проверьте токен, возможно он истек или неверный.

### 400 Bad Request (при регистрации)
```json
{
  "detail": "Username already registered"
}
```
**Решение:** Выберите другое имя пользователя.

## Следующие шаги

- [ ] Добавить роли (admin, user, guest)
- [ ] Добавить refresh tokens
- [ ] Добавить email для восстановления пароля
- [ ] Добавить rate limiting
- [ ] Добавить логирование попыток входа
