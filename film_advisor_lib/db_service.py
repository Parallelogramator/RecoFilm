from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import User, Movie, UserMovie, WatchStatusEnum

def add_user(session: Session, username: str) -> User:
    user = session.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        session.add(user)
        session.commit()
    return user

def add_movie(session: Session, movie_id: int, title: str, genres: str) -> Movie:
    movie = session.query(Movie).filter(Movie.id == movie_id).first()
    if movie:
        # Обновляем существующий фильм
        movie.title = title
        movie.genres = genres
    else:
        movie = Movie(id=movie_id, title=title, genres=genres)
        session.add(movie)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        movie = session.query(Movie).filter(Movie.id == movie_id).first()
    return movie

def add_user_movie_relation(
    session: Session,
    user_id: int,
    movie_id: int,
    status: WatchStatusEnum,
    rate: float = None
) -> UserMovie:
    relation = session.query(UserMovie).filter(
        UserMovie.user_id == user_id,
        UserMovie.movie_id == movie_id
    ).first()
    if relation:
        relation.status = status
        relation.rate = rate
    else:
        relation = UserMovie(
            user_id=user_id,
            movie_id=movie_id,
            status=status,
            rate=rate
        )
        session.add(relation)
    session.commit()
    return relation

def get_user_movies_grouped_by_status(session: Session, user_id: int) -> dict:
    movies = session.query(UserMovie.status, Movie.id, Movie.title, Movie.genres, UserMovie.rate).\
        join(Movie, Movie.id == UserMovie.movie_id).\
        filter(UserMovie.user_id == user_id).all()
    
    grouped = {
        "просмотрено": [],
        "запланировано": [],
        "смотрю": [],
        "брошено": []
    }
    
    for movie in movies:
        status = movie.status.value
        grouped[status].append({
            "movie_id": movie.id,
            "movie_name": movie.title,
            "genres": movie.genres.split("|") if movie.genres else [],
            "rate": movie.rate
        })
    
    return grouped