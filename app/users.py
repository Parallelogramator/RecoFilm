from fastapi import Depends, HTTPException, status, Response, APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os
import sys

from film_advisor_lib.main import get_movie_recommendations_by_user_id

from . import crud
from .database import get_db_dependency
from . import schemas_db
from . import models_api

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

@router.post("/", response_model=models_api.UserAPI, summary="Создать пользователя")
def api_create_user(user: models_api.UserCreateAPI, db: Session = Depends(get_db_dependency)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user_core_create = schemas_db.UserCreate(**user.model_dump())
    return crud.create_user(db=db, user=user_core_create)

@router.get("/{user_id}", response_model=models_api.UserAPI, summary="Получить пользователя по ID")
def api_read_user(user_id: int, db: Session = Depends(get_db_dependency)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/{user_id}/interactions/", response_model=models_api.UserMovieAPI,
          summary="Добавить взаимодействие")
def api_create_user_movie_interaction(
        user_id: int,
        interaction: models_api.UserMovieCreateAPI,
        db: Session = Depends(get_db_dependency)
):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_movie = crud.get_movie(db, movie_id=interaction.movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    interaction_core_create = schemas_db.UserMovieCreate(**interaction.model_dump())
    return crud.update_user_movie_interaction(db=db, user_id=user_id, interaction=interaction_core_create)



@router.delete("/{user_id}/interactions/", status_code=200,
               summary="Удалить взаимодействие")
def api_delete_user_movie_interaction(
        user_id: int,
        interaction: models_api.UserMovieCreateAPI,
        db: Session = Depends(get_db_dependency)
):
    deleted_interaction = crud.delete_user_movie_interaction(
        db=db, user_id=user_id, movie_id=interaction.movie_id
    )
    if not deleted_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    return {"detail": "Interaction deleted successfully"}


@router.get("/{user_id}/interactions/", response_model=List[models_api.UserMovieAPI],
         summary="Все взаимодействия пользователя")
def api_get_user_interactions(request: Request, user_id: int, db: Session = Depends(get_db_dependency)):
    interactions = crud.get_user_interactions(db=db, user_id=user_id)
    return templates.TemplateResponse("library.html", {"request": request, "interactions": interactions})

@router.get("/{user_id}/interactions/{status}", response_model=List[models_api.UserMovieAPI],
         summary="Все взаимодействия пользователя")
def api_get_user_interactions(request: Request, user_id: int, status: str, db: Session = Depends(get_db_dependency)):
    interactions = crud.get_user_interactions(db=db, user_id=user_id, status=status)
    return templates.TemplateResponse("library.html", {"request": request, "interactions": interactions})

@router.get("/{user_id}/recommendations/", response_model=List[models_api.MovieAPI],
         summary="Получить рекомендации")
def api_get_recommendations_for_user(request: Request, user_id: int, num_recs: int = Query(default=50, ge=1, le=100),
                                     db: Session = Depends(get_db_dependency)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        recommendations = get_movie_recommendations_by_user_id(user_id=user_id, count=num_recs)
        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations available: insufficient user data or movies.")
        return templates.TemplateResponse("recommendations.html", {"request": request, "recommendations": recommendations})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")