# app/main.py

"""
Основной файл приложения FastAPI.

Определяет экземпляр FastAPI, настраивает маршрутизаторы, шаблоны,
статические файлы и основные маршруты приложения.
"""

import os
from typing import Optional

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, users, movies
from app.database import create_db_and_tables, get_db_dependency

# --- Инициализация приложения FastAPI ---
app = FastAPI(
    title="RecoFilm",
    description="Система рекомендаций фильмов",
    version="2.0.0"
)

# Создаем таблицы в БД при запуске приложения (если их нет)
create_db_and_tables()

# --- Настройка шаблонов и статических файлов ---
# Указываем директорию для шаблонов Jinja2
templates = Jinja2Templates(directory="app/templates")
# Подключаем директорию static для раздачи статических файлов (CSS, JS)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static"
)


# --- Основные маршруты ---

@app.get("/", response_class=HTMLResponse)
def index(
        request: Request,
        limit: Optional[int] = 10,
        db: Session = Depends(get_db_dependency)
):
    """
    Отображает главную страницу со списком популярных фильмов.

    Args:
        request: Объект запроса FastAPI.
        limit: Количество фильмов для отображения.
        db: Сессия базы данных.

    Returns:
        HTML-ответ с отрендеренным шаблоном.
    """
    movies_list = crud.get_movies(db, skip=0, limit=limit)
    return templates.TemplateResponse(
        "index.html", {"request": request, "movies": movies_list}
    )


@app.get("/search", response_class=HTMLResponse)
def search(
        request: Request,
        name: Optional[str] = None,
        year: Optional[int] = None,
        limit: Optional[int] = 10,
        db: Session = Depends(get_db_dependency)
):
    """
    Выполняет поиск фильмов по названию и/или году и отображает результаты.

    Args:
        request: Объект запроса FastAPI.
        name: Название фильма для поиска.
        year: Год выпуска фильма для поиска.
        limit: Количество фильмов для отображения.
        db: Сессия базы данных.

    Returns:
        HTML-ответ с отрендеренным шаблоном.
    """
    movies_list = crud.search_movies(db, limit=limit, name=name, year=year)
    return templates.TemplateResponse(
        "index.html", {"request": request, "movies": movies_list}
    )


# --- Подключение маршрутизаторов ---
# Подключаем роутеры из других модулей для лучшей организации кода
app.include_router(users.router, tags=["users"], prefix="/users")
app.include_router(movies.router, tags=["movies"], prefix="/movies")
