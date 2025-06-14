# app/database.py

"""
Модуль для настройки и подключения к базе данных.

Определяет движок SQLAlchemy, фабрику сессий и функции-зависимости
для использования в FastAPI.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Настройка путей ---
# Определяем корень проекта для надежного указания пути к БД
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Создаем директорию для данных, если она не существует
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# --- Настройка подключения к БД ---
# URL для подключения к базе данных SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'movies.db')}"

# Создаем движок SQLAlchemy
# connect_args={"check_same_thread": False} требуется только для SQLite,
# чтобы разрешить использование БД в разных потоках (нужно для FastAPI)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем фабрику сессий, которая будет создавать новые сессии по запросу
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем базовый класс для декларативных моделей SQLAlchemy
Base = declarative_base()


def get_db_session() -> sessionmaker:
    """
    Создает и возвращает сессию БД. Вызывающий код отвечает за ее закрытие.

    Returns:
        Новая сессия SQLAlchemy.
    """
    return SessionLocal()


def get_db_dependency():
    """
    Зависимость FastAPI для получения сессии базы данных.

    Эта функция-генератор создает сессию для каждого запроса и гарантирует
    ее закрытие после завершения запроса.

    Yields:
        Сессия базы данных.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    """
    Создает все таблицы в базе данных.

    Использует метаданные из Base для создания таблиц, которые еще не существуют.
    Импорт моделей происходит внутри функции, чтобы избежать циклических зависимостей.
    """
    # Импортируем модели здесь, чтобы убедиться, что они зарегистрированы в Base.metadata
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created (if not exist) at {SQLALCHEMY_DATABASE_URL}")
