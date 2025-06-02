import pandas as pd
from sqlalchemy.orm import sessionmaker
from .database import engine, Base
from .models_db import Movie

# Настройка базы данных
Session = sessionmaker(bind=engine)
session = Session()

def load_movies():
    movies_file = "./ml-32m/movies.csv"
    try:
        print("Reading movies.csv...")
        movies_df = pd.read_csv(movies_file)
        print(f"Total movies in movies.csv: {len(movies_df)}")

        existing_ids = {row[0] for row in session.query(Movie.id).all()}
        new_movies = movies_df[~movies_df['movieId'].isin(existing_ids)]
        print(f"New movies to load: {len(new_movies)}")

        movies_to_insert = [
            {
                "id": row["movieId"],
                "title": row["title"],
                "genres_str": row["genres"]
            }
            for _, row in new_movies.iterrows()
        ]

        if movies_to_insert:
            session.bulk_insert_mappings(Movie, movies_to_insert)
            session.commit()
            print("Movies successfully loaded into movies table.")
        else:
            print("No new movies to load.")

        total_movies = session.query(Movie).count()
        print(f"Total movies in database: {total_movies}")

    except FileNotFoundError:
        print(f"Error: File {movies_file} not found.")
    except Exception as e:
        print(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    load_movies()