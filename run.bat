@echo off
call conda activate RecoFilm
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to activate Conda environment. Please run 'conda activate RecoFilm' manually.
    exit /b 1
)

uvicorn app.main:app --reload