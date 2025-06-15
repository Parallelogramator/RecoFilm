# app/schemas_db.py

"""
Внутренние Pydantic-схемы (модели данных).

Эти схемы используются внутри приложения, в основном в CRUD-функциях,
для четкого определения структуры данных, передаваемых между слоями
приложения. Они отделены от API-моделей для большей гибкости.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from .models_db import InteractionStatusEnum


# --- Схемы для User ---

class UserBase(BaseModel):
    """Базовая схема пользователя."""
    username: str
    email: Optional[str] = None


class UserCreate(UserBase):
    """Схема для создания нового пользователя."""
    pass


class UserCore(UserBase):
    """Основная схема пользователя, включающая ID."""
    id: int

    class Config:
        # Позволяет создавать экземпляр схемы из ORM-объекта
        from_attributes = True


# --- Схемы для Movie ---

class MovieBase(BaseModel):
    """Базовая схема фильма."""
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    rating_imdb: Optional[float] = None


class MovieCreate(MovieBase):
    """Схема для создания нового фильма."""
    pass


class MovieCore(MovieBase):
    """Основная схема фильма, включающая ID."""
    id: int

    class Config:
        from_attributes = True


# --- Схемы для UserMovie Interaction ---

class UserMovieBase(BaseModel):
    """Базовая схема взаимодействия."""
    movie_id: int
    status: InteractionStatusEnum


class UserMovieCreate(UserMovieBase):
    """Схема для создания нового взаимодействия."""
    pass


class UserMovieCore(UserMovieBase):
    """Основная схема взаимодействия, включающая ID и user_id."""
    id: int
    user_id: int

    class Config:
        from_attributes = True
