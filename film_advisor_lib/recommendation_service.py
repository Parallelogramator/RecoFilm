from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from .models_db import UserMovie, Movie, InteractionStatusEnum
from typing import List, Dict
import pickle
import os
from collections import defaultdict
from datetime import datetime
import time

def create_movies_ratings(
    movies_file: str = "./ml-32m/movies.csv",
    ratings_file: str = "./ml-32m/ratings.csv",
    cache_file: str = "movies_ratings.pkl",
    min_ratings: int = 10,
    min_avg_rating: float = 3.0
) -> dict:
    start_time = time.time()
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)
                cache_timestamp = cache_data.get("timestamp")
                movies_timestamp = os.path.getmtime(movies_file)
                ratings_timestamp = os.path.getmtime(ratings_file)
                if cache_timestamp >= max(movies_timestamp, ratings_timestamp):
                    print(f"Loaded cache: {time.time() - start_time:.2f} sec")
                    return cache_data["movies_dict"]
                print("Cache outdated, recalculating...")
        except Exception as e:
            print(f"Error loading cache: {e}. Recalculating...")

    try:
        import pandas as pd
        movies_df = pd.read_csv(movies_file)
        ratings_df = pd.read_csv(ratings_file, usecols=['movieId', 'rating'])

        rating_stats = ratings_df.groupby('movieId')['rating'].agg(['mean', 'count']).reset_index()
        rating_stats.columns = ['movieId', 'mean_rating', 'rating_count']
        rating_stats = rating_stats[
            (rating_stats['rating_count'] >= min_ratings) &
            (rating_stats['mean_rating'] >= min_avg_rating)
        ]
        movies_df = pd.merge(rating_stats, movies_df, on='movieId', how='inner')
        movies_df = movies_df[
            (movies_df['genres'] != '(no genres listed)') &
            (movies_df['genres'].notna())
        ]

        movies_dict = {
            row['movieId']: {
                "title": row['title'],
                "genres": row['genres'].split('|'),
                "mean_rating": row['mean_rating'],
                "rating_count": row['rating_count']
            }
            for _, row in movies_df.iterrows()
        }

        cache_data = {"movies_dict": movies_dict, "timestamp": datetime.now().timestamp()}
        with open(cache_file, "wb") as f:
            pickle.dump(cache_data, f)
        print(f"Cache saved to {cache_file}")
        print(f"Created movies_ratings: {time.time() - start_time:.2f} sec")
        return movies_dict
    except FileNotFoundError:
        print(f"Error: File {movies_file} or {ratings_file} not found.")
        return {}
    except Exception as e:
        print(f"Error processing data: {e}")
        return {}

def get_user_genre_profile(session: Session, user_id: int) -> Dict[str, float]:
    start_time = time.time()
    user_movies = (
        session.query(UserMovie.status, UserMovie.rate, Movie.genres_str)
        .join(Movie, Movie.id == UserMovie.movie_id)
        .filter(UserMovie.user_id == user_id)
        .all()
    )

    genre_weights = defaultdict(float)
    for status, rate, genres in user_movies:
        if not genres or genres == "(no genres listed)":
            continue
        genre_list = genres.split("|")
        weight = 0.0
        if status == InteractionStatusEnum.WATCHED:
            weight = rate if rate is not None else 1.0
        elif status == InteractionStatusEnum.LIKED:
            weight = 1.5
        elif status == InteractionStatusEnum.WANT_TO_WATCH:
            weight = 0.5
        elif status == InteractionStatusEnum.WATCHING:
            weight = 0.75
        elif status == InteractionStatusEnum.DROPPED:
            weight = -0.5
        for genre in genre_list:
            genre_weights[genre] += weight

    print(f"Created genre profile: {time.time() - start_time:.2f} sec")
    return dict(genre_weights)

def get_recommended_movies(
    session: Session,
    user_id: int,
    n: int,
    ratings_file: str = "./ml-32m/ratings.csv",
    movies_file: str = "./ml-32m/movies.csv",
    min_avg_rating: float = 3.0,
    min_ratings: int = 10
) -> List[Dict]:
    start_time = time.time()
    genre_profile = get_user_genre_profile(session, user_id)
    if not genre_profile:
        print("No genre preference data for user.")
        return []

    relevant_genres = [genre for genre, weight in genre_profile.items() if weight > 0]
    if not relevant_genres:
        print("No relevant genres for recommendations.")
        return []

    user_movie_ids = {movie.movie_id for movie in session.query(UserMovie.movie_id).filter(UserMovie.user_id == user_id).all()}
    movies_dict = create_movies_ratings(movies_file, ratings_file, min_ratings=min_ratings, min_avg_rating=min_avg_rating)
    if not movies_dict:
        print("Failed to load movie data. Recommendations not possible.")
        return []

    recommendations = []
    for movie_id, movie_data in movies_dict.items():
        if movie_id in user_movie_ids:
            continue
        if not any(genre in movie_data['genres'] for genre in relevant_genres):
            continue
        genre_score = sum(genre_profile.get(genre, 0.0) for genre in movie_data['genres'])
        final_score = genre_score * (movie_data['mean_rating'] / 5.0)
        recommendations.append({
            "movie_id": movie_id,
            "title": movie_data['title'],
            "genres": movie_data['genres'],
            "avg_rating": movie_data['mean_rating'],
            "score": final_score
        })

    recommendations.sort(key=lambda x: x['score'], reverse=True)
    result = recommendations[:n]
    print(f"Total recommendation time: {time.time() - start_time:.2f} sec")
    return result