from sqlalchemy.orm import Session
from typing import List, Optional, Set

from . import models_db, schemas_db
from .models_db import InteractionStatusEnum

# --- User CRUD ---
def get_user(db: Session, user_id: int) -> Optional[models_db.User]:
    return db.query(models_db.User).filter(models_db.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[models_db.User]:
    return db.query(models_db.User).filter(models_db.User.username == username).first()

def create_user(db: Session, user: schemas_db.UserCreate) -> models_db.User:
    db_user = models_db.User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Movie CRUD ---
def get_movie(db: Session, movie_id: int) -> Optional[models_db.Movie]:
    return db.query(models_db.Movie).filter(models_db.Movie.id == movie_id).first()

def get_movies(db: Session, skip: int = 0, limit: int = 100) -> List[models_db.Movie]:
    return db.query(models_db.Movie).offset(skip).limit(limit).all()

def create_movie(db: Session, movie: schemas_db.MovieCreate) -> models_db.Movie:
    db_movie = models_db.Movie(
        title=movie.title,
        year=movie.year,
        description=movie.description,
        rating_imdb=movie.rating_imdb
    )
    db_movie.genres = movie.genres
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[models_db.Movie]:
    if not movie_ids:
        return []
    return db.query(models_db.Movie).filter(models_db.Movie.id.in_(movie_ids)).all()


# --- UserMovie CRUD ---
def create_user_movie_interaction(
    db: Session, user_id: int, interaction: schemas_db.UserMovieCreate
) -> models_db.UserMovie:
    db_interaction = models_db.UserMovie(
        user_id=user_id,
        movie_id=interaction.movie_id,
        status=interaction.status
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

def get_user_interactions(db: Session, user_id: int, status: str = None) -> List[models_db.UserMovie]:
    if status:
        return db.query(models_db.UserMovie).filter(models_db.UserMovie.user_id == user_id).filter(models_db.UserMovie.status == status).all()
    else:
        return db.query(models_db.UserMovie).filter(models_db.UserMovie.user_id == user_id).all()

def get_user_liked_movies(db: Session, user_id: int) -> List[models_db.Movie]:
    return db.query(models_db.Movie)\
        .join(models_db.UserMovie, models_db.Movie.id == models_db.UserMovie.movie_id)\
        .filter(models_db.UserMovie.user_id == user_id)\
        .filter(models_db.UserMovie.status == InteractionStatusEnum.LIKED)\
        .all()

def get_user_interacted_movie_ids(db: Session, user_id: int) -> Set[int]:
    interactions = db.query(models_db.UserMovie.movie_id)\
        .filter(models_db.UserMovie.user_id == user_id)\
        .distinct()\
        .all()
    return {interaction.movie_id for interaction in interactions}