# app/models_api.py

"""
Модели Pydantic для валидации данных, приходящих через API.

Эти модели используются FastAPI для валидации входящих JSON-объектов
и для формирования исходящих ответов. Суффикс 'API' используется для
отличия от внутренних схем и моделей БД.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from .models_db import InteractionStatusEnum


# --- Модели для User ---

class UserBaseAPI(BaseModel):
    """Базовая модель пользователя для API."""
    username: str


class UserCreateAPI(UserBaseAPI):
    """Модель для создания нового пользователя через API."""
    pass


class UserAPI(UserBaseAPI):
    """Модель для отображения данных пользователя в ответах API."""
    id: int

    class Config:
        # Позволяет Pydantic-модели считывать данные напрямую из объектов SQLAlchemy
        from_attributes = True


# --- Модели для Movie ---

class MovieBaseAPI(BaseModel):
    """Базовая модель фильма для API."""
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    rating_imdb: Optional[float] = None


class MovieCreateAPI(MovieBaseAPI):
    """Модель для создания нового фильма через API."""
    pass


class MovieAPI(MovieBaseAPI):
    """Модель для отображения данных фильма в ответах API."""
    id: int

    class Config:
        from_attributes = True


# --- Модели для UserMovie Interaction ---

class UserMovieBaseAPI(BaseModel):
    """Базовая модель взаимодействия пользователя с фильмом для API."""
    movie_id: int
    status: InteractionStatusEnum


class UserMovieCreateAPI(UserMovieBaseAPI):
    """Модель для создания нового взаимодействия через API."""
    pass


class UserMovieAPI(UserMovieBaseAPI):
    """Модель для отображения данных о взаимодействии в ответах API."""
    id: int
    user_id: int

    class Config:
        from_attributes = True
