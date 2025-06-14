#!/bin/bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate film_advisor_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate Conda environment. Please run 'conda activate film_advisor_env' manually."
    exit 1
fi

python -c "from app.database import SessionLocal, engine; from sqlalchemy import inspect; inspector = inspect(engine); has_movies = 'movies' in inspector.get_table_names(); if not has_movies: from film_advisor_lib.load_all_movies import load_movies; load_movies()"
uvicorn app.main:app --reload