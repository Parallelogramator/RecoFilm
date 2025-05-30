import os
import sys
from typing import List

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse

from .database import get_db_dependency

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from . import crud, users, movies

app = FastAPI(
    title="RecoFilm",
    description="",
    version="2.0.0"
)


@app.get('/')
def index(db: Session = Depends(get_db_dependency)):
    movies = crud.get_movies(db, skip=0, limit=10)
    return movies


app.include_router(users.router, tags=["users"], prefix="/users")
app.include_router(movies.router, tags=["movies"], prefix="/movies")
