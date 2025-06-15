import subprocess
import os
import sys
import shutil
import time

CONDA_ENV_NAME = "RecoFilm"
ENV_FILE = "environment.yml"
PROJECT_ROOT = os.path.dirname(__file__)

def find_conda_executable():
    """Находит путь к исполняемому файлу Conda (conda.exe)."""
    # Поиск через CONDA_EXE переменную (самый надежный способ после активации)
    conda_exe = os.environ.get("CONDA_EXE")
    if conda_exe and os.path.exists(conda_exe):
        return conda_exe

    # Поиск в стандартных местах установки (для Windows)
    potential_paths = [
        os.path.join(os.environ.get('USERPROFILE', ''), 'Miniconda3', 'Scripts', 'conda.exe'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'Anaconda3', 'Scripts', 'conda.exe'),
        'C:\\Miniconda3\\Scripts\\conda.exe',
        'C:\\Anaconda3\\Scripts\\conda.exe',
        # Добавьте другие типичные пути, если Conda установлена не в USERPROFILE
        'C:\\ProgramData\\Miniconda3\\Scripts\\conda.exe',
        'C:\\ProgramData\\Anaconda3\\Scripts\\conda.exe'
    ]
    for path in potential_paths:
        if os.path.exists(path):
            return path

    # Поиск в PATH (как последний вариант)
    for path_dir in os.environ["PATH"].split(os.pathsep):
        conda_exec = os.path.join(path_dir, "conda.exe")
        if os.path.exists(conda_exec):
            return conda_exec
    return None


def run_command(command: list[str], cwd: str = None, check_returncode: bool = True) -> bool:
    print(f"Выполняется: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8', # Указываем UTF-8 для корректного вывода
            cwd=cwd,
            shell=False # Для большинства команд Conda shell=False более безопасно.
                        # Если Conda активирована, она должна быть в PATH.
        )
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
        process.wait()
        if check_returncode and process.returncode != 0:
            print(f"Ошибка выполнения команды. Код возврата: {process.returncode}")
            return False
        return True
    except FileNotFoundError:
        print(f"Ошибка: Команда '{command[0]}' не найдена. Проверьте PATH или корректность установки Conda.")
        return False
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False

def get_conda_envs(conda_path: str) -> list[str]:
    """Возвращает список имен существующих Conda-окружений."""
    result = subprocess.run([conda_path, "env", "list", "--json"], capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0:
        import json
        envs_data = json.loads(result.stdout)
        # Извлекаем только имена окружений (последний компонент пути)
        return [os.path.basename(env_path) for env_path in envs_data["envs"]]
    else:
        print(f"Ошибка при получении списка Conda окружений: {result.stderr}")
        return []

def main():
    print("Начало установки RecoFilm на хост-машину...")

    conda_path = find_conda_executable()
    if not conda_path:
        print("Ошибка: Conda не найдена. Пожалуйста, установите Miniconda или Anaconda.")
        print("Вы можете скачать Miniconda с: https://docs.conda.io/en/latest/miniconda.html")
        sys.exit(1)
    print(f"Используется Conda: {conda_path}")

    # Проверяем и удаляем существующее окружение
    # Получаем список окружений через найденный conda_path
    existing_envs = get_conda_envs(conda_path)
    if CONDA_ENV_NAME in existing_envs:
        print(f"Окружение Conda '{CONDA_ENV_NAME}' уже существует. Удаляем и пересоздаем...")
        # Используем conda_path для вызова conda env remove
        if not run_command([conda_path, "env", "remove", "-n", CONDA_ENV_NAME, "--yes"]):
            print("Не удалось удалить существующее Conda окружение. Попробуйте вручную 'conda env remove -n RecoFilm'.")
            sys.exit(1)

    print(f"\nСоздание Conda окружения '{CONDA_ENV_NAME}' из {ENV_FILE}...")
    # Используем conda_path для вызова conda env create
    if not run_command([conda_path, "env", "create", "-f", ENV_FILE, "--yes"]):
        print("Не удалось создать Conda окружение. Проверьте environment.yml и ваше интернет-соединение.")
        sys.exit(1)
    print(f"Conda окружение '{CONDA_ENV_NAME}' успешно создано.")

    # Очистка кэша Conda (опционально, можно добавить сюда или в run.sh)
    # print(f"\nОчистка кэша Conda...")
    # if not run_command([conda_path, "clean", "--all", "--yes"]):
    #    print("Не удалось очистить кэш Conda.")

    print("\n--- ВАЖНО: Настройка MySQL ---")
    print("Пожалуйста, убедитесь, что у вас установлен и запущен MySQL-сервер на вашей машине.")
    print("Вам также необходимо создать базу данных 'recofilm' и пользователя 'recofilm_user' (или использовать свои) с правами доступа.")
    print("Вы можете использовать SQL-скрипт 'init_mysql.sql' для начальной настройки.")
    print("Пример выполнения init_mysql.sql:")
    print(f"  В PowerShell: Get-Content {os.path.join(PROJECT_ROOT, 'init_mysql.sql')} | mysql -u root -p")
    print(f"  В CMD: mysql -u root -p < {os.path.join(PROJECT_ROOT, 'init_mysql.sql')}")
    print("После запуска MySQL и настройки базы данных, нажмите Enter для продолжения...")
    input()

    print("\nЗагрузка данных в базу данных...")
    # Путь к исполняемому файлу Python внутри Conda окружения
    # Убедитесь, что эта логика правильная для Windows (bin vs Scripts)
    # В Windows исполняемые файлы обычно в 'Scripts'
    python_in_env_dir = os.path.join(
        os.path.dirname(os.path.dirname(conda_path)), "envs", CONDA_ENV_NAME, "python.exe"
    )
    if not os.path.exists(python_in_env_dir):
        # Если python.exe не найден в корне окружения, поищите в Scripts
        python_in_env_dir = os.path.join(
            os.path.dirname(os.path.dirname(conda_path)), "envs", CONDA_ENV_NAME, "Scripts", "python.exe"
        )

    if not os.path.exists(python_in_env_dir):
        print(f"Ошибка: Не удалось найти python.exe в Conda окружении '{CONDA_ENV_NAME}'.")
        sys.exit(1)

    load_script_path = os.path.join(PROJECT_ROOT, "film_advisor_lib", "load_all_movies.py")

    # Использование `conda run` для выполнения скрипта в активированном окружении
    # Более надежный способ.
    if not run_command([conda_path, "run", "-n", CONDA_ENV_NAME, "python", load_script_path]):
        print("Не удалось загрузить данные в базу данных.")
        print("Если вы уже запускали этот скрипт ранее, данные могли быть уже загружены.")
        print("Проверьте файл 'error.log' в корне проекта для более подробной информации.")
        # sys.exit(1) # Не выходим, так как данные могли быть уже загружены

    print("\nУстановка завершена успешно!")
    print("Теперь вы можете запустить приложение командой: ./run.sh")
    print("Приложение будет доступно по адресу: http://localhost:8000")

if __name__ == "__main__":
    main()