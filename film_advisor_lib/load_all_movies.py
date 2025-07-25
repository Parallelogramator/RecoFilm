import json
import os
import sys

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models_db import Movie, User
from app.database import DATABASE_URL, Base
import kagglehub


def load_movies():
    dataset_path = kagglehub.dataset_download("rounakbanik/the-movies-dataset")
    movies_file = os.path.join(dataset_path, "movies_metadata.csv")

    try:
        print(f"Reading {movies_file}...")
        movies_df = pd.read_csv(movies_file, low_memory=False)
        print(f"Movies loaded: {len(movies_df)}")

        def parse_genres(genres_str):
            if pd.isna(genres_str) or genres_str == '':
                return ""
            try:
                genres_list = json.loads(genres_str.replace("'", "\""))
                genres = ",".join([g['name'] for g in genres_list if 'name' in g])
                return genres
            except Exception as e:
                print(f"Error parsing genres {genres_str}: {e}")
                return ""

        movies_df['genres_str'] = movies_df['genres'].apply(parse_genres)
        movies_df['year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year

        movies_to_load = movies_df[['id', 'title', 'year', 'genres_str', 'overview', 'vote_average']]
        movies_to_load = movies_to_load.rename(columns={
            'id': 'id',
            'title': 'title',
            'year': 'year',
            'genres_str': 'genres_str',
            'overview': 'description',
            'vote_average': 'rating_imdb'
        })

        # Clean data
        movies_to_load['id'] = pd.to_numeric(movies_to_load['id'], errors='coerce').astype('Int64')
        movies_to_load['year'] = movies_to_load['year'].fillna(0).astype('Int64')
        movies_to_load['rating_imdb'] = pd.to_numeric(movies_to_load['rating_imdb'], errors='coerce').fillna(0.0)
        movies_to_load['description'] = movies_to_load['description'].fillna('')
        movies_to_load = movies_to_load.dropna(subset=['id', 'title'])

        print(f"Cleaned movies to load: {len(movies_to_load)}")

        duplicate_ids = movies_to_load['id'].duplicated().sum()
        if duplicate_ids > 0:
            print(f"Warning: Found {duplicate_ids} duplicate ids. Removing duplicates...")
            movies_to_load = movies_to_load.drop_duplicates(subset=['id'], keep='first')

        # Initialize database
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create default user with ID 1 if not exists
        default_user = session.query(User).filter(User.id == 1).first()
        if not default_user:
            default_user = User(username="default_user")
            session.add(default_user)
            session.commit()
            print("Created default user with ID 1 and username 'default_user'")
        else:
            print("Default user with ID 1 already exists")

        # Update existing movies instead of dropping table
        existing_ids = {row[0] for row in session.query(Movie.id).all()}
        new_movies = movies_to_load[~movies_to_load['id'].isin(existing_ids)]
        print(f"Movies to load: {len(new_movies)}")

        movies_to_insert = new_movies.to_dict(orient='records')

        if movies_to_insert:
            try:
                for movie in movies_to_insert:
                    try:
                        session.merge(Movie(**movie))
                        session.commit()
                    except IntegrityError as e:
                        session.rollback()
                        print(f"Skipping movie ID {movie['id']} due to error: {e}")
                print("Movies successfully loaded.")
            except Exception as e:
                session.rollback()
                with open('error.log', 'w', encoding='utf-8') as f:
                    f.write(f"Error during insertion: {str(e)}\n")
                    import traceback
                    f.write(f"Traceback: {traceback.format_exc()}\n")
                print("Error during insertion. Check 'error.log'")
        else:
            print("No new movies to load.")

        total_movies = session.query(Movie).count()
        print(f"Total movies in database: {total_movies}")

    except FileNotFoundError:
        print(f"Error: File {movies_file} not found.")
    except Exception as e:
        with open('error.log', 'w', encoding='utf-8') as f:
            f.write(f"Error: {str(e)}\n")
            import traceback
            f.write(f"Traceback: {traceback.format_exc()}\n")
        print("Error occurred. Check 'error.log'")
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    load_movies()
