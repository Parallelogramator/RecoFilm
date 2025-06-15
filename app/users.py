from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models_api, schemas_db
from .crud import get_user_recommendations_movies
from .database import get_db_dependency
from .models_db import InteractionStatusEnum

try:
    from film_advisor_lib.main import get_movie_recommendations_by_user_id
except ImportError:
    print("Warning: film_advisor_lib not found. Recommendations will not work.")


    def get_movie_recommendations_by_user_id(user_id, count) -> list[int]:
        return []  # Заглушка, если библиотека отсутствует

# Создаем роутер и настраиваем шаблоны
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/", response_model=models_api.UserAPI, summary="Создать пользователя")
def api_create_user(
        user: models_api.UserCreateAPI,
        db: Session = Depends(get_db_dependency)
):
    """
    API-эндпоинт для создания нового пользователя.

    Args:
        user: Данные нового пользователя (username).
        db: Сессия базы данных.

    Raises:
        HTTPException: Если пользователь с таким именем уже существует.

    Returns:
        Созданный объект пользователя.
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    user_core_create = schemas_db.UserCreate(**user.model_dump())
    return crud.create_user(db=db, user=user_core_create)


@router.get("/{user_id}", response_model=models_api.UserAPI, summary="Получить пользователя по ID")
def api_read_user(user_id: int, db: Session = Depends(get_db_dependency)):
    """
    API-эндпоинт для получения информации о пользователе по ID.

    Args:
        user_id: ID пользователя.
        db: Сессия базы данных.

    Raises:
        HTTPException: Если пользователь не найден.

    Returns:
        Объект пользователя.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/{user_id}/interactions/", response_model=models_api.UserMovieAPI,
             summary="Добавить/обновить взаимодействие")
def api_create_or_update_user_movie_interaction(
        user_id: int,
        interaction: models_api.UserMovieCreateAPI,
        db: Session = Depends(get_db_dependency)
):
    """
    Создает или обновляет взаимодействие пользователя с фильмом.

    Args:
        user_id: ID пользователя.
        interaction: Данные о взаимодействии (movie_id, status).
        db: Сессия базы данных.

    Raises:
        HTTPException: Если пользователь или фильм не найдены.

    Returns:
        Созданный или обновленный объект взаимодействия.
    """
    # Проверяем существование пользователя и фильма
    if not crud.get_user(db, user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if not crud.get_movie(db, movie_id=interaction.movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")

    if interaction.status not in [e.value for e in InteractionStatusEnum]:
        raise HTTPException(status_code=422, detail=f"Invalid status: {interaction.status}")

    interaction_core_create = schemas_db.UserMovieCreate(**interaction.model_dump())
    return crud.update_user_movie_interaction(
        db=db, user_id=user_id, interaction=interaction_core_create
    )


@router.delete("/{user_id}/interactions/{movie_id}", status_code=status.HTTP_200_OK,
               summary="Удалить взаимодействие")
def api_delete_user_movie_interaction(
        user_id: int,
        movie_id: int,
        db: Session = Depends(get_db_dependency)
):
    """
    Удаляет взаимодействие пользователя с фильмом.

    Args:
        user_id: ID пользователя.
        movie_id: ID фильма, взаимодействие с которым удаляется.
        db: Сессия базы данных.

    Raises:
        HTTPException: Если взаимодействие не найдено.

    Returns:
        Сообщение об успешном удалении.
    """
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
    """
    Отображает HTML-страницу со всеми взаимодействиями пользователя.

    Args:
        request: Объект запроса.
        user_id: ID пользователя.
        db: Сессия базы данных.

    Returns:
        HTML-ответ со страницей "Библиотека".
    """
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
    """
    Отображает HTML-страницу с взаимодействиями пользователя, отфильтрованными по статусу.

    Args:
        request: Объект запроса.
        user_id: ID пользователя.
        status: Статус для фильтрации (e.g., 'liked', 'watched').
        db: Сессия базы данных.

    Returns:
        HTML-ответ со страницей "Библиотека".
    """
    interactions = crud.get_user_interactions(db=db, user_id=user_id, status=status)
    return templates.TemplateResponse(
        "library.html", {"request": request, "interactions": interactions}
    )


@router.get("/{user_id}/recommendations/", response_class=HTMLResponse,
            summary="Получить и отобразить рекомендации")
async def page_get_recommendations_for_user(
        request: Request,
        user_id: int,
        limit: int = Query(default=50, ge=1, le=100),
        db: Session = Depends(get_db_dependency)
):
    """
    Генерирует и отображает HTML-страницу с рекомендациями для пользователя.

    Args:
        request: Объект запроса.
        user_id: ID пользователя.
        limit: Количество рекомендаций.
        db: Сессия базы данных.

    Raises:
        HTTPException: Если пользователь не найден или произошла ошибка генерации.

    Returns:
        HTML-ответ со страницей рекомендаций.
    """
    if not crud.get_user(db, user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")
    try:
        movies_ids = get_movie_recommendations_by_user_id(user_id=user_id, count=limit)
        if not movies_ids:
            raise HTTPException(
                status_code=404,
                detail="No recommendations available: insufficient user data or movies."
            )
        recommendations = get_user_recommendations_movies(db, movies_ids)
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="No recommendations available: insufficient user data or movies."
            )
        return templates.TemplateResponse(
            "recommendations.html",
            {"request": request, "recommendations": recommendations}
        )
    except Exception as e:
        # Отлавливаем любые ошибки от рекомендательной системы
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
