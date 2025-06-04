import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'movies.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db_session():
    """Создает и возвращает сессию БД. Вызывающий код отвечает за ее закрытие."""
    return SessionLocal()


def get_db_dependency():
    """Зависимость FastAPI для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    from . import models_db
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created (if not exist) at {SQLALCHEMY_DATABASE_URL}")
