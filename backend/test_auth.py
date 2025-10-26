"""
Скрипт для тестирования аутентификации Comet Lab API.

Использование:
    python test_auth.py
"""

import requests
from datetime import datetime

API_URL = "http://localhost:8000"


def test_login(username: str, password: str):
    """Тестирует логин и возвращает токен"""
    print(f"\n🔐 Тестируем логин для пользователя: {username}")
    
    response = requests.post(
        f"{API_URL}/login",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Логин успешен!")
        print(f"📝 Токен (первые 50 символов): {token[:50]}...")
        return token
    else:
        print(f"❌ Ошибка логина: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_me(token: str):
    """Тестирует получение информации о текущем пользователе"""
    print(f"\n👤 Получаем информацию о текущем пользователе")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/me", headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Пользователь: {user['username']} (ID: {user['id']})")
        print(f"   Создан: {user['created_at']}")
        return user
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_observations(token: str):
    """Тестирует получение списка наблюдений"""
    print(f"\n🔭 Получаем список наблюдений")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/observations", headers=headers)
    
    if response.status_code == 200:
        observations = response.json()
        print(f"✅ Найдено наблюдений: {len(observations)}")
        if observations:
            print(f"   Первое: RA={observations[0]['ra_hours']}, Dec={observations[0]['dec_degrees']}")
        return observations
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_register(username: str, password: str):
    """Тестирует регистрацию нового пользователя"""
    print(f"\n📝 Регистрируем нового пользователя: {username}")
    
    response = requests.post(
        f"{API_URL}/register",
        json={"username": username, "password": password}
    )
    
    if response.status_code == 201:
        user = response.json()
        print(f"✅ Пользователь создан!")
        print(f"   ID: {user['id']}, Username: {user['username']}")
        return user
    elif response.status_code == 400:
        print(f"⚠️  Пользователь уже существует")
        return None
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_unauthorized():
    """Тестирует доступ без токена"""
    print(f"\n🚫 Пытаемся получить данные без токена")
    
    response = requests.get(f"{API_URL}/observations")
    
    if response.status_code == 401:
        print(f"✅ Правильно! Получили 401 Unauthorized")
        print(f"   {response.json()}")
    else:
        print(f"❌ Неожиданный код: {response.status_code}")


def main():
    print("=" * 60)
    print("🚀 Тестирование аутентификации Comet Lab API")
    print("=" * 60)
    
    # Тест 1: Попытка без токена
    test_unauthorized()
    
    # Тест 2: Логин как admin
    admin_token = test_login("admin", "admin")
    if admin_token:
        test_me(admin_token)
        test_observations(admin_token)
    
    # Тест 3: Логин как user
    user_token = test_login("user", "user")
    if user_token:
        test_me(user_token)
        test_observations(user_token)
    
    # Тест 4: Неверный пароль
    test_login("admin", "wrongpassword")
    
    # Тест 5: Регистрация нового пользователя
    test_register("testuser", "testpass123")
    
    # Тест 6: Попытка повторной регистрации
    test_register("admin", "anypassword")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения!")
        print("Убедитесь что сервер запущен: docker compose up")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
