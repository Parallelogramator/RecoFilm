# install.py
import subprocess
import os
import sys
import shutil
from typing import Optional

CONDA_ENV_NAME = "film_advisor_env"
ENV_FILE = "environment.yml" # В корне проекта

# Пути теперь указывают внутрь папки app
APP_DIR = os.path.join(os.path.dirname(__file__), "app")
DB_PATH_DIR = os.path.join(APP_DIR, "db")
DB_FILE = os.path.join(DB_PATH_DIR, "test_movies.db")
INITIAL_DATA_CSV = os.path.join(APP_DIR, "initial_data", "movies.csv")

def run_command(command: list[str], cwd: Optional[str] = None) -> bool:
    print(f"Executing: {' '.join(command)}")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', cwd=cwd)
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
        process.wait()
        if process.returncode != 0:
            print(f"Error executing command. Return code: {process.returncode}")
            return False
        return True
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is it in your PATH?")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def find_conda():
    conda_exe = shutil.which("conda")
    if conda_exe: return conda_exe
    home = os.path.expanduser("~")
    possible_paths = [
        os.path.join(home, "anaconda3", "bin", "conda"), os.path.join(home, "miniconda3", "bin", "conda"),
        os.path.join(home, "Anaconda3", "Scripts", "conda.exe"), os.path.join(home, "Miniconda3", "Scripts", "conda.exe")
    ]
    for path in possible_paths:
        if os.path.exists(path): return path
    return None

def create_db_and_load_data():
    """
    Создает БД и загружает начальные данные.
    Это требует, чтобы окружение было уже создано,
    и Python мог импортировать app.database и app.services.
    Этот скрипт должен запускаться Python-интерпретатором,
    который может найти эти модули (например, из корня проекта).
    """
    print("Creating database and loading initial data...")
    os.makedirs(DB_PATH_DIR, exist_ok=True)

    # Добавляем корень проекта в sys.path, чтобы импорты из app работали
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from app import database, services, auth # Импортируем после добавления в sys.path
        from app.database import SessionLocal

        database.init_db() # Создаст таблицы, если их нет

        with next(database.get_db_session_context()) as db_session:
            _ = auth.get_default_user(db_session) # Создаст пользователя по умолчанию
            if os.path.exists(INITIAL_DATA_CSV):
                services.load_initial_movies_from_csv(db_session, INITIAL_DATA_CSV)
            else:
                print(f"Initial data file {INITIAL_DATA_CSV} not found. Skipping initial data load.")
        print("Database setup and initial data load (if any) complete.")
    except ImportError as e:
        print(f"Failed to import app modules for DB setup: {e}")
        print("Ensure Conda environment is created and you are running install.py from project root.")
        print("Or, activate the environment first and then run this part of the script.")
        return False # Указываем на ошибку
    except Exception as e:
        print(f"An error occurred during DB setup: {e}")
        return False
    return True


def main():
    print("Starting Film Advisor installation...")
    conda_path = find_conda()
    if not conda_path:
        print("Error: Conda executable not found. Please ensure Conda is installed and in your PATH.")
        sys.exit(1)
    print(f"Using Conda: {conda_path}")

    # 1. Создание Conda-окружения
    print(f"\nCreating Conda environment '{CONDA_ENV_NAME}' from {ENV_FILE}...")
    if not run_command([conda_path, "env", "create", "-f", ENV_FILE, "--force"]):
        print("Failed to create Conda environment. Please check 'environment.yml' and Conda setup.")
        sys.exit(1)
    print(f"Conda environment '{CONDA_ENV_NAME}' created successfully.")

    # 2. Установка зависимостей в созданное окружение (на всякий случай, если yml не все покрыл)
    # Это можно сделать и через environment.yml, но так надежнее для локальных пакетов
    # conda_run = [conda_path, "run", "-n", CONDA_ENV_NAME]
    # print("\nEnsuring all dependencies are installed...")
    # if not run_command(conda_run + ["python", "-m", "pip", "install", "-r", "requirements.txt"]): # Если есть requirements.txt
    #     print("Failed to install dependencies from requirements.txt.")
    #     # sys.exit(1) # Не критично, если environment.yml полный

    # 3. Создание базы данных и загрузка данных
    # Этот шаг выполняется Python-ом из текущего (базового) окружения, но импортирует из app.
    # Либо можно было бы активировать среду и запустить отдельный скрипт.
    # Для простоты, делаем здесь, полагаясь на sys.path.
    print("\nSetting up database...")
    if not create_db_and_load_data():
        print("Database setup failed. Please check logs.")
        # Можно решить, прерывать ли установку
        # sys.exit(1)

    print("\nInstallation complete!")
    print(f"To run the application:")
    print(f"1. Activate the Conda environment: conda activate {CONDA_ENV_NAME}")
    print(f"2. Run the application: python app/main.py (or use run.sh/run.bat)")

if __name__ == "__main__":
    main()