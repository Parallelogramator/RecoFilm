# app/models_db.py

"""
Модели базы данных SQLAlchemy.

Определяют структуру таблиц в базе данных: User, Movie и UserMovie.
"""

import enum

from sqlalchemy import (Column, Enum as SQLAlchemyEnum, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from .database import Base


class InteractionStatusEnum(str, enum.Enum):
    """Перечисление возможных статусов взаимодействия пользователя с фильмом."""
    WATCHED = "watched"
    LIKED = "liked"
    WANT_TO_WATCH = "want_to_watch"
    DROPPED = "dropped"
    WATCHING = "watching"


class User(Base):
    """Модель таблицы 'users'."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)

    # Связь "один ко многим" с таблицей взаимодействий
    interactions = relationship("UserMovie", back_populates="user")


class Movie(Base):
    """Модель таблицы 'movies'."""
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=True)
    # Жанры хранятся как строка, разделенная запятыми
    genres_str = Column("genres", String, nullable=True)
    description = Column(Text, nullable=True)
    rating_imdb = Column(Float, nullable=True)

    # Связь "один ко многим" с таблицей взаимодействий
    interactions = relationship("UserMovie", back_populates="movie")

    @property
    def genres(self) -> list[str]:
        """
        Property для получения жанров в виде списка строк.

        Читает строку из `genres_str` и преобразует ее в список.
        """
        if self.genres_str:
            # Разделяем строку по запятой и удаляем лишние пробелы
            return [genre.strip() for genre in self.genres_str.split(',') if genre.strip()]
        return []

    @genres.setter
    def genres(self, value: list[str]):
        """
        Property-setter для установки жанров из списка строк.

        Преобразует список в строку, разделенную запятыми, и сохраняет в `genres_str`.
        """
        if value:
            self.genres_str = ",".join(genre.strip() for genre in value if genre.strip())
        else:
            self.genres_str = ""


class UserMovie(Base):
    """Модель таблицы 'user_movie' (таблица связей)."""
    __tablename__ = "user_movie"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    status = Column(SQLAlchemyEnum(InteractionStatusEnum), nullable=False)
    rate = Column(Float)

    # Связь "многие к одному" с таблицей пользователей
    user = relationship("User", back_populates="interactions")
    # Связь "многие к одному" с таблицей фильмов
    movie = relationship("Movie", back_populates="interactions")
