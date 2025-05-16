import os
import sys
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# Импорты из общих модулей
from . import crud
from .database import get_db_dependency
from . import schemas_db
from . import models_api

try:
    from film_advisor_lib import recommender
except ImportError as e:
    print(f"Error importing film_advisor_lib in backend: {e}")
    raise

app = FastAPI(
    title="Film Advisor Backend (Shared DB)",
    description="Backend API с общей БД и вызовом рекомендаций по user_id.",
    version="2.0.0"
)


@app.get('/')
def index(db: Session = Depends(get_db_dependency)):
    movies = crud.get_movies(db, skip=0, limit=10)
    return movies


@app.post("/users/", response_model=models_api.UserAPI, summary="Создать пользователя")
def api_create_user(user: models_api.UserCreateAPI, db: Session = Depends(get_db_dependency)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    # Преобразуем API схему в Core схему для CRUD
    user_core_create = schemas_db.UserCreate(**user.model_dump())
    return crud.create_user(db=db, user=user_core_create)


@app.get("/users/{user_id}", response_model=models_api.UserAPI, summary="Получить пользователя по ID")
def api_read_user(user_id: int, db: Session = Depends(get_db_dependency)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/movies/", response_model=models_api.MovieAPI, summary="Добавить фильм")
def api_create_movie(movie: models_api.MovieCreateAPI, db: Session = Depends(get_db_dependency)):
    movie_core_create = schemas_db.MovieCreate(**movie.model_dump())
    return crud.create_movie(db=db, movie=movie_core_create)


@app.get("/movies/", response_model=List[models_api.MovieAPI], summary="Получить список фильмов")
def api_read_movies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_dependency)):
    movies = crud.get_movies(db, skip=skip, limit=limit)
    return movies


@app.get("/movies/{movie_id}", response_model=models_api.MovieAPI, summary="Получить фильм по ID")
def api_read_movie(movie_id: int, db: Session = Depends(get_db_dependency)):
    db_movie = crud.get_movie(db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@app.post("/users/{user_id}/interactions/", response_model=models_api.UserMovieInteractionAPI,
          summary="Добавить взаимодействие")
def api_create_user_movie_interaction(
        user_id: int,
        interaction: models_api.UserMovieInteractionCreateAPI,
        db: Session = Depends(get_db_dependency)
):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_movie = crud.get_movie(db, movie_id=interaction.movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    interaction_core_create = schemas_db.UserMovieInteractionCreate(**interaction.model_dump())
    return crud.create_user_movie_interaction(db=db, user_id=user_id, interaction=interaction_core_create)


@app.get("/users/{user_id}/interactions/", response_model=List[models_api.UserMovieInteractionAPI],
         summary="Все взаимодействия пользователя")
def api_get_user_interactions(user_id: int, db: Session = Depends(get_db_dependency)):
    interactions = crud.get_user_interactions(db=db, user_id=user_id)
    return interactions


@app.get("/users/{user_id}/recommendations/", response_model=List[models_api.MovieAPI],
         summary="Получить рекомендации")
def api_get_recommendations_for_user(
        user_id: int,
        num_recs: int = Query(default=5, ge=1, le=20),
):
    temp_db = next(get_db_dependency())
    try:
        db_user = crud.get_user(temp_db, user_id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found for recommendations")
    finally:
        temp_db.close()

    recommended_movies_db_models = recommender.get_movie_recommendations_by_user_id(
        user_id=user_id,
        num_recommendations=num_recs
    )

    return recommended_movies_db_models
