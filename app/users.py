from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models_api, schemas_db
from .database import get_db_dependency
from .models_db import InteractionStatusEnum

try:
    from film_advisor_lib.main import get_movie_recommendations_by_user_id
except ImportError:
    print("Warning: film_advisor_lib not found. Recommendations will not work.")
    def get_movie_recommendations_by_user_id(user_id, count):
        return []  # Заглушка, если библиотека отсутствует

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/", response_model=models_api.UserAPI, summary="Создать пользователя")
def api_create_user(
    user: models_api.UserCreateAPI,
    db: Session = Depends(get_db_dependency)
):
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

@router.post("/{user_id}/interactions/", response_model=models_api.UserMovieAPI)
def api_create_or_update_user_movie_interaction(
    user_id: int,
    interaction: models_api.UserMovieCreateAPI,
    db: Session = Depends(get_db_dependency)
):
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Received interaction: {interaction.model_dump()}")
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    movie = crud.get_movie(db, movie_id=interaction.movie_id)
    if not movie:
        raise HTTPException(status_code=422, detail=f"Movie with ID {interaction.movie_id} not found")
    if interaction.status not in [e.value for e in InteractionStatusEnum]:
        raise HTTPException(status_code=422, detail=f"Invalid status: {interaction.status}")
    interaction_core = schemas_db.UserMovieCreate(**interaction.model_dump())
    relation = crud.update_user_movie_interaction(db=db, user_id=user_id, interaction=interaction_core)
    logger.info(f"Returned interaction: {relation.status}")
    return relation

@router.delete("/{user_id}/interactions/{movie_id}", status_code=status.HTTP_200_OK,
               summary="Удалить взаимодействие")
def api_delete_user_movie_interaction(
    user_id: int,
    movie_id: int,
    db: Session = Depends(get_db_dependency)
):
    deleted_interaction = crud.delete_user_movie_interaction(
        db=db, user_id=user_id, movie_id=movie_id
    )
    if not deleted_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return {"detail": "Interaction deleted successfully"}

@router.get(
    "/{user_id}/interactions/",
    response_class=HTMLResponse,
    summary="Страница со всеми взаимодействиями пользователя"
)
def page_get_all_user_interactions(
    request: Request, user_id: int, db: Session = Depends(get_db_dependency)
):
    interactions = crud.get_user_interactions(db=db, user_id=user_id)
    return templates.TemplateResponse(
        "library.html", {"request": request, "interactions": interactions}
    )

@router.get(
    "/{user_id}/interactions/{status}",
    response_class=HTMLResponse,
    summary="Страница с взаимодействиями по статусу"
)
def page_get_user_interactions_by_status(
    request: Request, user_id: int, status: str, db: Session = Depends(get_db_dependency)
):
    interactions = crud.get_user_interactions(db=db, user_id=user_id, status=status)
    return templates.TemplateResponse(
        "library.html", {"request": request, "interactions": interactions}
    )

@router.get("/{user_id}/recommendations/", response_class=HTMLResponse)
async def page_get_recommendations_for_user(
    request: Request,
    user_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db_dependency)
):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    recommendations = get_movie_recommendations_by_user_id(user_id=user_id, count=limit)
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations available")
    normalized_recommendations = [
        {
            "id": rec.get("movie_id"),  # Текущий movie_id из рекомендаций
            "title": rec.get("title", "Unknown"),
            "genres": rec.get("genres", []),
            "year": None,
            "rating_imdb": rec.get("avg_rating"),
            "description": rec.get("description", "No description"),
            "status": None
        }
        for rec in recommendations
    ]
    movie_ids_in_db = [movie.id for movie in crud.get_all_movies(db) if movie.id is not None]
    valid_recommendations = [rec for rec in normalized_recommendations if rec["id"] in movie_ids_in_db]
    if not valid_recommendations:
        raise HTTPException(
            status_code=500,
            detail="No valid recommendations with proper IDs available."
        )
    return templates.TemplateResponse(
        "recommendations.html",
        {"request": request, "recommendations": valid_recommendations}
    )