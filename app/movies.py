from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List

from . import crud
from .database import get_db_dependency
from . import schemas_db
from . import models_api

router = APIRouter()


@router.post("/movies/", response_model=models_api.MovieAPI, summary="Добавить фильм")
def api_create_movie(movie: models_api.MovieCreateAPI, db: Session = Depends(get_db_dependency)):
    movie_core_create = schemas_db.MovieCreate(**movie.model_dump())
    return crud.create_movie(db=db, movie=movie_core_create)


@router.get("/movies/", response_model=List[models_api.MovieAPI], summary="Получить список фильмов")
def api_read_movies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_dependency)):
    movies = crud.get_movies(db, skip=skip, limit=limit)
    return movies


@router.get("/movies/{movie_id}", response_model=models_api.MovieAPI, summary="Получить фильм по ID")
def api_read_movie(movie_id: int, db: Session = Depends(get_db_dependency)):
    db_movie = crud.get_movie(db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie