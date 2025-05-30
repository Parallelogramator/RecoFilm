from sqlalchemy import Column, Integer, String, Float, Text, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from .database import Base

class WatchStatusEnum(enum.Enum):
    watched = "просмотрено"
    planned = "запланировано"
    dropped = "брошено"
    watching = "смотрю"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    movies = relationship("UserMovie", back_populates="user")


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    genres_str = Column("genres", String, nullable=True)

    description = Column(Text, nullable=True)
    rating_imdb = Column(Float, nullable=True)
    interactions = relationship("UserMovieInteraction", back_populates="movie")

    @property
    def genres(self) -> list[str]:
        if self.genres_str:
            return [genre.strip() for genre in self.genres_str.split(',') if genre.strip()]
        return []

    @genres.setter
    def genres(self, value: list[str]):
        self.genres_str = ",".join(genre.strip() for genre in value if genre.strip()) if value else ""

class UserMovie(Base):
    __tablename__ = "user_movies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    status = Column(SQLAlchemyEnum(WatchStatusEnum))
    rate = Column(Float)

    user = relationship("User", back_populates="movies")
    movie = relationship("Movie", back_populates="interactions")