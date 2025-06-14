# app/movies.py

"""
Маршрутизатор (роутер) FastAPI для операций с фильмами.

Предоставляет API-эндпоинты для создания и получения информации о фильмах.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, models_api, schemas_db
from .database import get_db_dependency

# Создаем новый роутер для эндпоинтов, связанных с фильмами
router = APIRouter()


@router.post("/", response_model=models_api.MovieAPI, summary="Добавить фильм")
def api_create_movie(
        movie: models_api.MovieCreateAPI, db: Session = Depends(get_db_dependency)
):
    """
    API-эндпоинт для создания нового фильма.

    Args:
        movie: Данные нового фильма из тела запроса.
        db: Сессия базы данных (зависимость).

    Returns:
        Созданный объект фильма.
    """
    # Преобразуем API-модель в схему для CRUD-функции
    movie_core_create = schemas_db.MovieCreate(**movie.model_dump())
    return crud.create_movie(db=db, movie=movie_core_create)


@router.get("/", response_model=List[models_api.MovieAPI], summary="Получить список фильмов")
def api_read_movies(
        skip: int = 0, limit: int = 10, db: Session = Depends(get_db_dependency)
):
    """
    API-эндпоинт для получения списка фильмов с пагинацией.

    Args:
        skip: Количество пропускаемых фильмов.
        limit: Максимальное количество возвращаемых фильмов.
        db: Сессия базы данных (зависимость).

    Returns:
        Список фильмов.
    """
    movies_list = crud.get_movies(db, skip=skip, limit=limit)
    return movies_list


@router.get("/{movie_id}", response_model=models_api.MovieAPI, summary="Получить фильм по ID")
def api_read_movie(movie_id: int, db: Session = Depends(get_db_dependency)):
    """
    API-эндпоинт для получения одного фильма по его ID.

    Args:
        movie_id: ID фильма для поиска.
        db: Сессия базы данных (зависимость).

    Raises:
        HTTPException: Если фильм с указанным ID не найден.

    Returns:
        Найденный объект фильма.
    """
    db_movie = crud.get_movie(db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie
