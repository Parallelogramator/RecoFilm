@echo off
call conda activate RecoFilm
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to activate Conda environment. Please run 'conda activate RecoFilm' manually.
    exit /b 1
)

python -c "from app.database import SessionLocal, engine; from sqlalchemy import inspect; inspector = inspect(engine); has_movies = 'movies' in inspector.get_table_names(); if not has_movies: from film_advisor_lib.load_all_movies import load_movies; load_movies()"
uvicorn app.main:app --reload