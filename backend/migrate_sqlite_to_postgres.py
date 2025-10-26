"""
Скрипт для миграции данных из SQLite в PostgreSQL.
Запускайте его после настройки PostgreSQL, если у вас есть существующие данные в SQLite.

Использование:
    python migrate_sqlite_to_postgres.py

Убедитесь, что:
1. PostgreSQL запущен и доступен
2. В .env установлен DATABASE_URL для PostgreSQL
3. Файл data/app.db существует и содержит данные
"""

import os
import sys
from pathlib import Path

# Добавляем путь к модулям app
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import SQLModel, create_engine, Session, select
from app.models import Observation, OrbitSolution


def migrate_data():
    """Переносит данные из SQLite в PostgreSQL"""
    
    # Путь к старой SQLite базе
    sqlite_path = Path(__file__).parent.parent / "data" / "app.db"
    
    if not sqlite_path.exists():
        print(f"❌ SQLite база не найдена: {sqlite_path}")
        print("Миграция не требуется - начинайте с чистой PostgreSQL базы.")
        return
    
    # Подключение к SQLite
    sqlite_url = f"sqlite:///{sqlite_path}"
    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    
    # Подключение к PostgreSQL из переменных окружения
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ Переменная DATABASE_URL не установлена!")
        print("Установите её в .env файле или переменных окружения.")
        return
    
    if postgres_url.startswith("sqlite"):
        print("❌ DATABASE_URL указывает на SQLite, а не PostgreSQL!")
        print("Обновите DATABASE_URL в .env файле.")
        return
    
    postgres_engine = create_engine(postgres_url, echo=False, pool_pre_ping=True)
    
    print("🔄 Начинаем миграцию данных...")
    
    # Создаем таблицы в PostgreSQL
    print("📦 Создаём таблицы в PostgreSQL...")
    SQLModel.metadata.create_all(postgres_engine)
    
    # Читаем данные из SQLite
    with Session(sqlite_engine) as sqlite_session:
        observations = sqlite_session.exec(select(Observation)).all()
        orbit_solutions = sqlite_session.exec(select(OrbitSolution)).all()
        
        print(f"📊 Найдено наблюдений: {len(observations)}")
        print(f"📊 Найдено решений орбит: {len(orbit_solutions)}")
        
        if not observations and not orbit_solutions:
            print("ℹ️  SQLite база пустая - нечего мигрировать.")
            return
        
        # Записываем в PostgreSQL
        with Session(postgres_engine) as postgres_session:
            # Миграция наблюдений
            if observations:
                print("🔄 Переносим наблюдения...")
                for obs in observations:
                    new_obs = Observation(
                        id=obs.id,
                        ra_hours=obs.ra_hours,
                        dec_degrees=obs.dec_degrees,
                        observation_time=obs.observation_time,
                        photo_path=obs.photo_path,
                        created_at=obs.created_at,
                    )
                    postgres_session.add(new_obs)
                
                postgres_session.commit()
                print(f"✅ Перенесено {len(observations)} наблюдений")
            
            # Миграция решений орбит
            if orbit_solutions:
                print("🔄 Переносим решения орбит...")
                for solution in orbit_solutions:
                    new_solution = OrbitSolution(
                        id=solution.id,
                        semi_major_axis_au=solution.semi_major_axis_au,
                        eccentricity=solution.eccentricity,
                        inclination_deg=solution.inclination_deg,
                        raan_deg=solution.raan_deg,
                        arg_periapsis_deg=solution.arg_periapsis_deg,
                        perihelion_time=solution.perihelion_time,
                        closest_approach_time=solution.closest_approach_time,
                        closest_distance_km=solution.closest_distance_km,
                        relative_speed_kms=solution.relative_speed_kms,
                        source_observation_ids=solution.source_observation_ids,
                        created_at=solution.created_at,
                    )
                    postgres_session.add(new_solution)
                
                postgres_session.commit()
                print(f"✅ Перенесено {len(orbit_solutions)} решений орбит")
    
    print("\n🎉 Миграция завершена успешно!")
    print("\n💡 Рекомендации:")
    print("1. Проверьте данные в PostgreSQL через приложение")
    print("2. Если всё работает, можете удалить папку data/ с SQLite базой")
    print("3. Фотографии в папке uploads/ остаются на месте")


if __name__ == "__main__":
    try:
        migrate_data()
    except Exception as e:
        print(f"\n❌ Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
