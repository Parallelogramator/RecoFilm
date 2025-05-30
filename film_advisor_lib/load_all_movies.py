import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Movie
from database import Base

# Настройка базы данных
engine = create_engine("sqlite:///filmtracker.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def load_movies():
    movies_file = "./ml-32m/movies.csv"
    try:
        # Читаем movies.csv
        print("Читаем movies.csv...")
        movies_df = pd.read_csv(movies_file)
        print(f"Всего фильмов в movies.csv: {len(movies_df)}")

        # Получаем существующие ID из all_movies
        existing_ids = {row[0] for row in session.query(Movie.id).all()}

        # Фильтруем новые фильмы
        new_movies = movies_df[~movies_df['movieId'].isin(existing_ids)]
        print(f"Новых фильмов для загрузки: {len(new_movies)}")

        # Подготавливаем данные для bulk insert
        movies_to_insert = [
            {
                "id": row["movieId"],
                "title": row["title"],
                "genres": row["genres"]
            }
            for _, row in new_movies.iterrows()
        ]

        # Вставляем фильмы
        if movies_to_insert:
            session.bulk_insert_mappings(Movie, movies_to_insert)
            session.commit()
            print("Фильмы успешно загружены в таблицу all_movies.")
        else:
            print("Нет новых фильмов для загрузки.")

        # Проверяем общее количество фильмов
        total_movies = session.query(Movie).count()
        print(f"Всего фильмов в all_movies: {total_movies}")

    except FileNotFoundError:
        print(f"Ошибка: Файл {movies_file} не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_movies()