# заглушка

import os
import sys
from typing import List, Set
from sqlalchemy.orm import Session

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from app import crud, models_db
    from app.database import get_db_session
except ImportError as e:
    print(f"Error importing app_core in recommender: {e}")
    raise


def get_movie_recommendations_by_user_id(
        user_id: int,
        num_recommendations: int = 5
) -> List[models_db.Movie]:
    """
    Получает рекомендации для пользователя по его ID.
    Функция сама получает сессию БД и извлекает необходимые данные.
    Это просто заглушка, демонстрирующая, как она будет получать данные.
    """
    db: Session = get_db_session()
    recommendations: List[models_db.Movie] = []

    try:
        print(f"[Recommender] Запрос рекомендаций для user_id: {user_id}")
        user = crud.get_user(db, user_id)
        if not user:
            print(f"[Recommender] Пользователь {user_id} не найден.")
            return []

        liked_movies: List[models_db.Movie] = crud.get_user_liked_movies(db, user_id)
        if not liked_movies:
            print(f"[Recommender] У пользователя {user_id} нет понравившихся фильмов.")

            all_movies = crud.get_movies(db, limit=num_recommendations)
            return all_movies  # Пример

        liked_movie_ids: Set[int] = {movie.id for movie in liked_movies}
        liked_genres: Set[str] = set()
        for movie in liked_movies:
            for genre in movie.genres:
                liked_genres.add(genre.lower())

        print(f"[Recommender] Понравившиеся жанры: {liked_genres}")

        interacted_movie_ids = crud.get_user_interacted_movie_ids(db, user_id)

        all_db_movies = crud.get_movies(db, limit=200)

        candidate_movies = []
        for movie in all_db_movies:
            if movie.id not in interacted_movie_ids:
                candidate_movies.append(movie)

        scored_candidates = []
        for movie in candidate_movies:
            movie_genres_lower = {genre.lower() for genre in movie.genres}
            common_genres_count = len(liked_genres.intersection(movie_genres_lower))
            if common_genres_count > 0:
                scored_candidates.append({"movie_obj": movie, "score": common_genres_count})

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        recommendations = [item["movie_obj"] for item in scored_candidates[:num_recommendations]]
        print(f"[Recommender] Рекомендовано {len(recommendations)} фильмов.")

    except Exception as e:
        print(f"[Recommender] Ошибка при получении рекомендаций: {e}")
    finally:
        db.close()

    return recommendations
