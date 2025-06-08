from sqlalchemy.orm import Session
from .models import UserMovie, Movie
from typing import List, Dict
import pandas as pd
from collections import defaultdict
import time
from app.models_db import InteractionStatusEnum


def get_movies_data(session: Session, min_avg_rating: float = 3.0, min_ratings: int = 1) -> pd.DataFrame:
    """Получает данные о фильмах из базы с фильтрацией по рейтингу."""
    start_time = time.time()
    try:
        # Запрашиваем фильмы с количеством взаимодействий
        movies = session.query(
            Movie.id.label('movieId'),
            Movie.title,
            Movie.genres_str.label('genres'),
            Movie.rating_imdb.label('mean_rating')
        ).all()

        if not movies:
            print("No movies found in database.")
            return pd.DataFrame()

        # Преобразуем в DataFrame
        movies_df = pd.DataFrame([
            {
                'movieId': movie.movieId,
                'title': movie.title,
                'genres': movie.genres or '',
                'mean_rating': movie.mean_rating or 0.0,
                'rating_count': 1  # У нас нет данных о количестве оценок, ставим 1
            }
            for movie in movies
        ])

        # Фильтруем по минимальному рейтингу
        movies_df = movies_df[
            (movies_df['mean_rating'] >= min_avg_rating) &
            (movies_df['genres'] != '') &
            (movies_df['genres'].notna())
            ]

        print(f"Loaded {len(movies_df)} movies from database in {time.time() - start_time:.2f} sec")
        return movies_df
    except Exception as e:
        print(f"Error loading movies from database: {e}")
        raise


def get_user_genre_profile(session: Session, user_id: int) -> dict:
    """Создаёт профиль жанров пользователя на основе его взаимодействий."""
    user_ratings = (
        session.query(UserMovie.status, Movie.genres_str)
        .join(Movie, UserMovie.movie_id == Movie.id)
        .filter(UserMovie.user_id == user_id)
        .all()
    )

    if not user_ratings:
        return {}

    genre_counts = {}
    total_weight = 0.0

    for status, genres in user_ratings:
        weight = 1.0
        if status == InteractionStatusEnum.WATCHED:
            weight = 2.0
        elif status == InteractionStatusEnum.LIKED:
            weight = 1.5
        elif status == InteractionStatusEnum.DROPPED:
            weight = 0.5
        total_weight += weight
        if genres:
            for genre in genres.split(","):
                genre = genre.strip()
                if genre:
                    genre_counts[genre] = genre_counts.get(genre, 0) + weight

    if total_weight == 0:
        return {}

    genre_profile = {genre: count / total_weight for genre, count in genre_counts.items()}
    return genre_profile


def get_top_n_by_genres(
        df: pd.DataFrame,
        genres: List[str],
        genre_weights: Dict[str, float],
        exclude_movie_ids: set,
        n: int = 10
) -> pd.DataFrame:
    """Возвращает топ-N фильмов по жанрам с учётом весов."""
    start_time = time.time()
    filtered_df = df[
        ~df['movieId'].isin(exclude_movie_ids) &
        df['genres'].apply(
            lambda x: any(genre in x.split(',') for genre in genres) if pd.notna(x) else False
        )
        ].copy()

    filtered_df['genre_score'] = filtered_df['genres'].apply(
        lambda x: sum(genre_weights.get(genre.strip(), 0.0) for genre in x.split(','))
    )
    filtered_df['final_score'] = filtered_df['genre_score'] * (filtered_df['mean_rating'] / 10.0)
    top_n = filtered_df.sort_values(by='final_score', ascending=False).head(n)
    print(f"get_top_n_by_genres: {time.time() - start_time:.2f} sec")
    return top_n[['movieId', 'title', 'mean_rating', 'genres', 'final_score']]


def get_recommended_movies(
        session: Session,
        user_id: int,
        n: int,
        min_avg_rating: float = 3.0,
        min_ratings: int = 1
) -> List[Dict]:
    """Формирует список рекомендованных фильмов для пользователя."""
    start_time = time.time()
    genre_profile = get_user_genre_profile(session, user_id)
    if not genre_profile:
        print("No genre preferences found for user.")
        return []

    relevant_genres = [genre for genre, weight in genre_profile.items() if weight > 0]
    if not relevant_genres:
        print("No relevant genres for recommendations.")
        return []

    user_movie_ids = {row.movie_id for row in
                      session.query(UserMovie.movie_id).filter(UserMovie.user_id == user_id).all()}

    try:
        movies_df = get_movies_data(session, min_avg_rating=min_avg_rating, min_ratings=min_ratings)
        if movies_df.empty:
            print("No movies available for recommendations.")
            return []

        top_n = get_top_n_by_genres(movies_df, relevant_genres, genre_profile, user_movie_ids, n=n)
        result = [
            {
                "movie_id": int(row['movieId']),
                "title": row['title'],
                "genres": row['genres'].split(',') if row['genres'] else [],
                "avg_rating": float(row['mean_rating']),
                "score": float(row['final_score'])
            }
            for _, row in top_n.iterrows()
        ]
        print(f"Total recommendation time: {time.time() - start_time:.2f} sec")
        return result
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        raise