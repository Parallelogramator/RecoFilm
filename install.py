# install.py
import os
import shutil
import subprocess
import sys
from typing import Optional

CONDA_ENV_NAME = "RecoFilm"
ENV_FILE = "environment.yml"

PROJECT_ROOT = os.path.dirname(__file__)
DB_PATH_DIR = os.path.join(PROJECT_ROOT, "data")
DB_FILE = os.path.join(DB_PATH_DIR, "movies.db")


def run_command(command: list[str], cwd: Optional[str] = None, shell: bool = False) -> bool:
    print(f"Executing: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            cwd=cwd,
            shell=shell
        )
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
    if conda_exe:
        return conda_exe
    home = os.path.expanduser("~")
    possible_paths = [
        os.path.join(home, "anaconda3", "bin", "conda"),
        os.path.join(home, "miniconda3", "bin", "conda"),
        os.path.join(home, "Anaconda3", "Scripts", "conda.exe"),
        os.path.join(home, "Miniconda3", "Scripts", "conda.exe")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def get_conda_envs():
    conda_path = find_conda()
    if not conda_path:
        return []
    result = subprocess.run(
        [conda_path, "env", "list"],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    if result.returncode != 0:
        print("Error listing Conda environments.")
        return []
    envs = [
        line.split()[0]
        for line in result.stdout.splitlines()
        if line and not line.startswith("#") and line.split()
    ]
    return envs


def install_pip_dependencies():
    print("Installing pip dependencies...")
    conda_path = find_conda()
    if not conda_path:
        print("Error: Conda not found.")
        return False
    # Получаем путь к Python в окружении RecoFilm
    env_path = os.path.join(os.path.dirname(os.path.dirname(conda_path)), "envs", CONDA_ENV_NAME)
    python_exe = os.path.join(env_path, "Scripts", "python.exe" if os.name == 'nt' else "bin", "python")
    pip_exe = os.path.join(env_path, "Scripts", "pip.exe" if os.name == 'nt' else "bin", "pip")
    if not os.path.exists(python_exe):
        print(f"Error: Python executable not found at {python_exe}")
        return False
    # Устанавливаем kagglehub и pydantic
    return run_command([pip_exe, "install", "pydantic", "kagglehub"])


def create_db_and_load_data():
    print("Creating database and loading data...")
    os.makedirs(DB_PATH_DIR, exist_ok=True)

    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    try:
        from app import database
        database.create_db_and_tables()

        db_session = database.SessionLocal()
        try:
            print("Loading Kaggle dataset...")
            load_movies_script = os.path.join(PROJECT_ROOT, "film_advisor_lib", "load_all_movies.py")
            if os.path.exists(load_movies_script):
                # Используем Python из текущего окружения
                run_command([sys.executable, load_movies_script], cwd=PROJECT_ROOT)
            else:
                print(f"Error: {load_movies_script} not found.")
        finally:
            db_session.close()
        print("Database setup complete.")
    except ImportError as e:
        print(f"Failed to import app modules: {e}")
        print("Ensure you are using the Python interpreter from 'conda activate RecoFilm'.")
        return False
    except Exception as e:
        print(f"Error during DB setup: {e}")
        return False
    return True


def main():
    print("Starting Film Advisor installation...")
    conda_path = find_conda()
    if not conda_path:
        print("Error: Conda executable not found. Ensure Conda is installed.")
        sys.exit(1)
    print(f"Using Conda: {conda_path}")

    if CONDA_ENV_NAME in get_conda_envs():
        print(f"Conda environment '{CONDA_ENV_NAME}' exists. Removing and recreating...")
        run_command([conda_path, "env", "remove", "-n", CONDA_ENV_NAME])

    print(f"\nCreating Conda environment '{CONDA_ENV_NAME}'...")
    if not run_command([conda_path, "env", "create", "-f", ENV_FILE]):
        print("Failed to create Conda environment.")
        sys.exit(1)
    print(f"Conda environment '{CONDA_ENV_NAME}' created.")

    print("\nInstalling pip dependencies...")
    if not install_pip_dependencies():
        print("Failed to install pip dependencies.")
        sys.exit(1)

    print("\nSetting up database...")
    if not create_db_and_load_data():
        print("Database setup failed.")
        sys.exit(1)

    print("\nInstallation complete!")
    print(f"To run the application:")
    print(f"1. Activate environment: conda activate {CONDA_ENV_NAME}")
    print(f"2. Run: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
