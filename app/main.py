import os
import sys
from typing import List, Optional
from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db_dependency, create_db_and_tables
from app import crud, users, movies

app = FastAPI(
    title="RecoFilm",
    description="Система рекомендаций фильмов",
    version="2.0.0"
)

create_db_and_tables()
# Настройка шаблонов и статических файлов
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, limit: Optional[int] = 10, db: Session = Depends(get_db_dependency)):
    movies = crud.get_movies(db, skip=0, limit=limit)
    return templates.TemplateResponse("index.html", {"request": request, "movies": movies})


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, name: Optional[str] = None, year: Optional[int] = None, db: Session = Depends(get_db_dependency)):
    movies = crud.search_movies(db, name=name, year=year)
    return templates.TemplateResponse("index.html", {"request": request, "movies": movies})

app.include_router(users.router, tags=["users"], prefix="/users")
app.include_router(movies.router, tags=["movies"], prefix="/movies")