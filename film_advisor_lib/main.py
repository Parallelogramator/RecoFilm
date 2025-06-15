import time

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models_db import InteractionStatusEnum
from .database import SessionLocal, engine, Base
from .db_service import add_user, add_movie, add_user_movie_relation, get_user_movies_grouped_by_status
from .models import Movie, UserMovie
from .recommendation_service import get_recommended_movies, get_user_genre_profile

Base.metadata.create_all(bind=engine)


def print_user_movies(session: Session, user_id: int, username: str):
    print(f"\nФильмы пользователя {username}:")
    data = get_user_movies_grouped_by_status(session, user_id)
    for status, movies in data.items():
        print(f"{status}:")
        if not movies:
            print("  (пусто)")
        for movie in movies:
            print(
                f"  - {movie['movie_name']} (ID: {movie['movie_id']}, Оценка: {movie['rate']}, Жанры: {movie['genres']})")


def get_movie_recommendations_by_user_id(user_id: int, count: int) -> list[int]:
    session = SessionLocal()
    try:
        recommendations = get_recommended_movies(session, user_id, n=count)
        return recommendations
    finally:
        session.close()


def main():
    session = SessionLocal()
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Таблицы в базе данных:", tables)
        if 'movies' not in tables or 'users' not in tables or 'user_movie' not in tables:
            raise Exception("Не все таблицы созданы. Проверьте models.py и Base.metadata.create_all")

        print("\nЗагружаем фильмы...")
        from load_all_movies import load_movies
        load_movies()
        total_movies = session.query(Movie).count()
        print(f"Всего фильмов в базе: {total_movies}")

        print("\nДобавляем пользователей...")
        user1 = add_user(session, "alex_silkov")
        user2 = add_user(session, "maria_nova")
        print(f"Создан пользователь: {user1.username} (ID: {user1.id})")
        print(f"Создан пользователь: {user2.username} (ID: {user2.id})")

        print("\nДобавляем фильмы...")
        movie1 = add_movie(session, movie_id=2571, title="Matrix", genres="Action,Sci-Fi")
        movie2 = add_movie(session, movie_id=72998, title="Avatar", genres="Action,Adventure")
        movie3 = add_movie(session, movie_id=79132, title="Inception", genres="Sci-Fi,Thriller")
        print(f"Добавлен фильм: {movie1.title} (ID: {movie1.id})")
        print(f"Добавлен фильм: {movie2.title} (ID: {movie2.id})")
        print(f"Добавлен фильм: {movie3.title} (ID: {movie3.id})")

        print("\nДобавляем связи между пользователями и фильмами...")
        add_user_movie_relation(session, user1.id, movie1.id, InteractionStatusEnum.WATCHED, rate=5.0)
        add_user_movie_relation(session, user1.id, movie2.id, InteractionStatusEnum.WANT_TO_WATCH, rate=None)
        add_user_movie_relation(session, user2.id, movie1.id, InteractionStatusEnum.WATCHING, rate=4.0)
        add_user_movie_relation(session, user2.id, movie3.id, InteractionStatusEnum.WATCHED, rate=4.5)
        print("Связи добавлены.")

        print_user_movies(session, user1.id, user1.username)
        print_user_movies(session, user2.id, user2.username)

        print("\nУдаляем фильм Matrix у пользователя maria_nova...")
        session.query(UserMovie).filter(
            UserMovie.user_id == user2.id,
            UserMovie.movie_id == movie1.id
        ).delete()
        session.commit()
        print("Связь удалена.")

        print_user_movies(session, user1.id, user1.username)
        print_user_movies(session, user2.id, user2.username)

        print(f"\nЖанровый профиль {user1.username}:")
        print(get_user_genre_profile(session, user1.id))
        print(f"\nЖанровый профиль {user2.username}:")
        print(get_user_genre_profile(session, user2.id))

        print(f"\nРекомендации для {user1.username} (топ-5 фильмов):")
        start_time = time.time()
        recommendations = get_recommended_movies(session, user1.id, n=5)
        elapsed_time = time.time() - start_time
        if not recommendations:
            print("  Нет рекомендаций: недостаточно данных.")
        for rec in recommendations:
            print(
                f"  - {rec['title']} (ID: {rec['movie_id']}, Средний рейтинг: {rec['avg_rating']:.2f}, Жанры: {rec['genres']}, Скор: {rec['score']:.2f})")
        print(f"Время выполнения рекомендаций: {elapsed_time:.2f} секунд")

        print(f"\nРекомендации для {user2.username} (топ-5 фильмов):")
        start_time = time.time()
        recommendations = get_recommended_movies(session, user2.id, n=5)
        elapsed_time = time.time() - start_time
        if not recommendations:
            print("  Нет рекомендаций: недостаточно данных.")
        for rec in recommendations:
            print(
                f"  - {rec['title']} (ID: {rec['movie_id']}, Средний рейтинг: {rec['avg_rating']:.2f}, Жанры: {rec['genres']}, Скор: {rec['score']:.2f})")
        print(f"Время выполнения рекомендаций: {elapsed_time:.2f} секунд")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
