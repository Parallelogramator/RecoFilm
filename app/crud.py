# app/crud.py

"""
Модуль для операций CRUD (Create, Read, Update, Delete) с базой данных.

Содержит функции для взаимодействия с моделями User, Movie и UserMovie.
"""

from typing import List, Optional, Set

from sqlalchemy.orm import Session

from . import models_db, schemas_db
from .models_db import InteractionStatusEnum


# --- CRUD операции для Пользователей (User) ---

def get_user(db: Session, user_id: int) -> Optional[models_db.User]:
    """
    Получает пользователя из БД по его ID.

    Args:
        db: Сессия базы данных.
        user_id: Идентификатор пользователя.

    Returns:
        Объект пользователя или None, если пользователь не найден.
    """
    # Выполняем запрос к таблице User, фильтруя по ID
    return db.query(models_db.User).filter(models_db.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models_db.User]:
    """
    Получает пользователя из БД по его имени (username).

    Args:
        db: Сессия базы данных.
        username: Имя пользователя.

    Returns:
        Объект пользователя или None, если пользователь не найден.
    """
    # Выполняем запрос к таблице User, фильтруя по username
    return db.query(models_db.User).filter(models_db.User.username == username).first()


def create_user(db: Session, user: schemas_db.UserCreate) -> models_db.User:
    """
    Создает нового пользователя в БД.

    Args:
        db: Сессия базы данных.
        user: Pydantic-схема с данными для создания пользователя.

    Returns:
        Созданный объект пользователя.
    """
    # Создаем экземпляр модели SQLAlchemy
    db_user = models_db.User(username=user.username)
    # Добавляем объект в сессию
    db.add(db_user)
    # Сохраняем изменения в БД
    db.commit()
    # Обновляем объект, чтобы получить ID, сгенерированный БД
    db.refresh(db_user)
    return db_user


# --- CRUD операции для Фильмов (Movie) ---

def get_movie(db: Session, movie_id: int) -> Optional[models_db.Movie]:
    """
    Получает фильм из БД по его ID.

    Args:
        db: Сессия базы данных.
        movie_id: Идентификатор фильма.

    Returns:
        Объект фильма или None, если фильм не найден.
    """
    return db.query(models_db.Movie).filter(models_db.Movie.id == movie_id).first()


def get_movies(db: Session, skip: int = 0, limit: int = 100) -> List[models_db.Movie]:
    """
    Получает список фильмов с пагинацией.

    Args:
        db: Сессия базы данных.
        skip: Количество записей, которое нужно пропустить.
        limit: Максимальное количество записей для возврата.

    Returns:
        Список объектов фильмов.
    """
    # Запрос с пропуском (offset) и ограничением (limit)
    return db.query(models_db.Movie).offset(skip).limit(limit).all()


def search_movies(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        year: Optional[int] = None
) -> List[models_db.Movie]:
    """
    Ищет фильмы по названию и/или году выпуска.

    Args:
        db: Сессия базы данных.
        skip: Количество записей для пропуска.
        limit: Максимальное количество записей для возврата.
        name: Часть названия фильма для поиска.
        year: Год выпуска фильма.

    Returns:
        Список найденных фильмов.
    """
    # Создаем базовый запрос
    query = db.query(models_db.Movie)

    # Если указано имя, добавляем фильтр по названию (поиск подстроки)
    if name is not None:
        query = query.filter(models_db.Movie.title.contains(name))

    # Если указан год, добавляем фильтр по году выпуска
    if year is not None:
        query = query.filter(models_db.Movie.year == year)

    # Применяем пагинацию и возвращаем результат
    return query.offset(skip).limit(limit).all()


def create_movie(db: Session, movie: schemas_db.MovieCreate) -> models_db.Movie:
    """
    Создает новый фильм в БД.

    Args:
        db: Сессия базы данных.
        movie: Pydantic-схема с данными для создания фильма.

    Returns:
        Созданный объект фильма.
    """
    # Создаем объект модели SQLAlchemy из данных схемы
    db_movie = models_db.Movie(
        title=movie.title,
        year=movie.year,
        description=movie.description,
        rating_imdb=movie.rating_imdb,
        genres=movie.genres  # Используем property-setter для жанров
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[models_db.Movie]:
    """
    Получает список фильмов по списку их ID.

    Args:
        db: Сессия базы данных.
        movie_ids: Список идентификаторов фильмов.

    Returns:
        Список объектов фильмов.
    """
    if not movie_ids:
        return []
    # Используем оператор `in_` для эффективного поиска по списку ID
    return db.query(models_db.Movie).filter(models_db.Movie.id.in_(movie_ids)).all()


# --- CRUD операции для Взаимодействий (UserMovie) ---

def get_user_movie_interaction(
        db: Session, user_id: int, movie_id: int
) -> Optional[models_db.UserMovie]:
    """
    Получает конкретное взаимодействие пользователя с фильмом.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        movie_id: ID фильма.

    Returns:
        Объект взаимодействия или None, если он не найден.
    """
    # Ищем запись по составному ключу user_id и movie_id
    return db.query(models_db.UserMovie).filter(
        models_db.UserMovie.user_id == user_id,
        models_db.UserMovie.movie_id == movie_id
    ).first()


def update_user_movie_interaction(
        db: Session, user_id: int, interaction: schemas_db.UserMovieCreate
) -> models_db.UserMovie:
    """
    Создает или обновляет взаимодействие пользователя с фильмом.

    Если взаимодействие уже существует, обновляет его статус.
    Если нет - создает новое.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        interaction: Схема с данными о взаимодействии (movie_id, status).

    Returns:
        Созданный или обновленный объект взаимодействия.
    """
    # Проверяем, существует ли уже такое взаимодействие
    db_interaction = get_user_movie_interaction(
        db, user_id=user_id, movie_id=interaction.movie_id
    )

    if db_interaction:
        # Если да, обновляем его статус
        db_interaction.status = interaction.status
    else:
        # Если нет, создаем новую запись
        db_interaction = models_db.UserMovie(
            user_id=user_id,
            movie_id=interaction.movie_id,
            status=interaction.status
        )
        db.add(db_interaction)

    # Сохраняем изменения и обновляем объект
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


def delete_user_movie_interaction(
        db: Session, user_id: int, movie_id: int
) -> Optional[models_db.UserMovie]:
    """
    Удаляет существующее взаимодействие пользователя с фильмом.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        movie_id: ID фильма.

    Returns:
        Удаленный объект взаимодействия или None, если он не был найден.
    """
    db_interaction = get_user_movie_interaction(db, user_id=user_id, movie_id=movie_id)

    if db_interaction:
        db.delete(db_interaction)
        db.commit()

    return db_interaction


def get_user_interactions(
        db: Session, user_id: int, status: Optional[str] = None
) -> List[models_db.UserMovie]:
    """
    Получает все взаимодействия пользователя, опционально фильтруя по статусу.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        status: Статус для фильтрации (например, 'liked').

    Returns:
        Список взаимодействий пользователя.
    """
    query = db.query(models_db.UserMovie).filter(models_db.UserMovie.user_id == user_id)
    if status:
        query = query.filter(models_db.UserMovie.status == status)
    return query.all()


def get_user_liked_movies(db: Session, user_id: int) -> List[models_db.Movie]:
    """
    Получает список фильмов, которые пользователь отметил как 'liked'.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.

    Returns:
        Список понравившихся фильмов.
    """
    # Выполняем JOIN между таблицами Movie и UserMovie
    return (
        db.query(models_db.Movie)
        .join(models_db.UserMovie, models_db.Movie.id == models_db.UserMovie.movie_id)
        .filter(models_db.UserMovie.user_id == user_id)
        .filter(models_db.UserMovie.status == InteractionStatusEnum.LIKED)
        .all()
    )


def get_user_interacted_movie_ids(db: Session, user_id: int) -> Set[int]:
    """
    Получает множество ID фильмов, с которыми пользователь взаимодействовал.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.

    Returns:
        Множество (set) ID фильмов.
    """
    # Выбираем только уникальные movie_id для указанного пользователя
    interactions = (
        db.query(models_db.UserMovie.movie_id)
        .filter(models_db.UserMovie.user_id == user_id)
        .distinct()
        .all()
    )
    # Преобразуем список кортежей в множество для быстрого доступа
    return {interaction.movie_id for interaction in interactions}
