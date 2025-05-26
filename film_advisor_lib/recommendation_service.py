from sqlalchemy.orm import Session
from .models import UserMovie, AllMovie, WatchStatusEnum
from typing import List, Dict
import pandas as pd
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
    min_avg_rating: float = 3.0,
    chunksize: int = 5000000
) -> pd.DataFrame:
    """Создаёт и кэширует DataFrame с фильмами и средними рейтингами."""
    start_time = time.time()
    # Проверяем, существует ли кэш и актуален ли он
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)
                cache_timestamp = cache_data.get("timestamp")
                movies_timestamp = os.path.getmtime(movies_file)
                ratings_timestamp = os.path.getmtime(ratings_file)
                if cache_timestamp >= max(movies_timestamp, ratings_timestamp):
                    print(f"Загрузка кэша фильмов: {time.time() - start_time:.2f} сек")
                    return cache_data["movies_df"]
                print("Кэш фильмов устарел, пересчитываем...")
        except Exception as e:
            print(f"Ошибка при загрузке кэша фильмов: {e}. Пересчитываем...")
    
    # Загружаем и обрабатываем данные
    try:
        movies_df = pd.read_csv(movies_file)
        ratings_df = pd.read_csv(ratings_file, usecols=['movieId', 'rating'], chunksize=chunksize)
        
        # Вычисляем средние рейтинги и количество оценок
        rating_stats = pd.concat(
            chunk.groupby('movieId')['rating'].agg(['mean', 'count'])
            for chunk in ratings_df
        ).groupby('movieId').sum()
        rating_stats.columns = ['mean_rating', 'rating_count']
        rating_stats = rating_stats.reset_index()
        
        # Фильтруем по минимальному количеству оценок и рейтингу
        rating_stats = rating_stats[
            (rating_stats['rating_count'] >= min_ratings) &
            (rating_stats['mean_rating'] >= min_avg_rating)
        ]
        
        # Объединяем с фильмами
        movies_df = pd.merge(rating_stats, movies_df, on='movieId', how='inner')
        
        # Исключаем фильмы без жанров
        movies_df = movies_df[
            (movies_df['genres'] != '(no genres listed)') &
            (movies_df['genres'].notna())
        ]
        
        # Сохраняем в кэш
        cache_data = {
            "movies_df": movies_df,
            "timestamp": datetime.now().timestamp()
        }
        with open(cache_file, "wb") as f:
            pickle.dump(cache_data, f)
        print(f"Кэш фильмов сохранён в {cache_file}")
        print(f"Создание movies_ratings: {time.time() - start_time:.2f} сек")
        return movies_df
    except FileNotFoundError:
        print(f"Ошибка: Файл {movies_file} или {ratings_file} не найден.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        return pd.DataFrame()

def get_user_genre_profile(session: Session, user_id: int) -> Dict[str, float]:
    """Создаёт жанровый профиль пользователя на основе его фильмов."""
    start_time = time.time()
    user_movies = (
        session.query(UserMovie.status, UserMovie.rate, AllMovie.genres)
        .join(AllMovie, AllMovie.id == UserMovie.movie_id)
        .filter(UserMovie.user_id == user_id)
        .all()
    )

    genre_weights = defaultdict(float)
    for status, rate, genres in user_movies:
        if not genres or genres == "(no genres listed)":
            continue
        
        genre_list = genres.split("|")
        if status == WatchStatusEnum.watched:
            weight = rate if rate is not None else 1.0
        elif status == WatchStatusEnum.planned:
            weight = 0.5
        elif status == WatchStatusEnum.watching:
            weight = 0.75
        elif status == WatchStatusEnum.dropped:
            weight = -0.5
        
        for genre in genre_list:
            genre_weights[genre] += weight
    
    print(f"Создание жанрового профиля: {time.time() - start_time:.2f} сек")
    return dict(genre_weights)

def get_top_n_by_genres(
    df: pd.DataFrame,
    genres: List[str],
    genre_weights: Dict[str, float],
    exclude_movie_ids: set,
    n: int = 10
) -> pd.DataFrame:
    """
    Возвращает топ-N фильмов по среднему рейтингу и жанровому скору, исключая указанные фильмы.
    
    :param df: DataFrame с колонками ['movieId', 'mean_rating', 'title', 'genres', 'rating_count']
    :param genres: Список жанров для фильтрации
    :param genre_weights: Словарь с весами жанров из профиля пользователя
    :param exclude_movie_ids: Множество movieId для исключения
    :param n: Количество фильмов в топе
    :return: DataFrame с топ-N фильмами
    """
    start_time = time.time()
    filtered_df = df[
        ~df['movieId'].isin(exclude_movie_ids) &
        df['genres'].apply(
            lambda x: any(genre in x.split('|') for genre in genres) if pd.notna(x) else False
        )
    ].copy()
    
    # Вычисляем жанровый скор
    filtered_df['genre_score'] = filtered_df['genres'].apply(
        lambda x: sum(genre_weights.get(genre, 0.0) for genre in x.split('|'))
    )
    
    # Комбинируем жанровый скор и рейтинг
    filtered_df['final_score'] = filtered_df['genre_score'] * (filtered_df['mean_rating'] / 5.0)
    
    # Сортируем по финальному скору
    top_n = filtered_df.sort_values(by='final_score', ascending=False).head(n)
    
    print(f"get_top_n_by_genres: {time.time() - start_time:.2f} сек")
    return top_n[['movieId', 'title', 'mean_rating', 'genres', 'final_score']]

def get_recommended_movies(
    session: Session,
    user_id: int,
    n: int,
    ratings_file: str = "./ml-32m/ratings.csv",
    movies_file: str = "./ml-32m/movies.csv",
    min_avg_rating: float = 3.0,
    min_ratings: int = 10
) -> List[Dict]:
    """
    Возвращает список из n рекомендованных фильмов для пользователя.
    Каждый фильм: {"movie_id": int, "title": str, "genres": list, "avg_rating": float}.
    """
    start_time = time.time()
    
    # Получаем жанровый профиль пользователя
    genre_profile = get_user_genre_profile(session, user_id)
    if not genre_profile:
        print("Нет данных о жанровых предпочтениях пользователя.")
        return []
    
    # Получаем релевантные жанры (с положительным весом)
    relevant_genres = [genre for genre, weight in genre_profile.items() if weight > 0]
    if not relevant_genres:
        print("Нет релевантных жанров для рекомендаций.")
        return []
    
    # Получаем фильмы пользователя (чтобы исключить их)
    user_movie_ids = {
        movie.movie_id
        for movie in session.query(UserMovie.movie_id)
        .filter(UserMovie.user_id == user_id)
        .all()
    }
    
    # Загружаем фильмы с рейтингами
    movies_df = create_movies_ratings(movies_file, ratings_file, min_ratings=min_ratings, min_avg_rating=min_avg_rating)
    if movies_df.empty:
        print("Не удалось загрузить данные фильмов. Рекомендации невозможны.")
        return []
    
    # Получаем топ-N фильмов
    top_n = get_top_n_by_genres(movies_df, relevant_genres, genre_profile, user_movie_ids, n=n)
    
    # Формируем результат
    result = [
        {
            "movie_id": int(row['movieId']),
            "title": row['title'],
            "genres": row['genres'].split('|'),
            "avg_rating": row['mean_rating'],
            "score": row['final_score']
        }
        for _, row in top_n.iterrows()
    ]
    
    print(f"Общее время рекомендаций: {time.time() - start_time:.2f} сек")
    return result