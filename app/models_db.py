from sqlalchemy import Column, Integer, String, Float, Text, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    interactions = relationship("UserMovieInteraction", back_populates="user")


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
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


class InteractionStatusEnum(str, enum.Enum):
    WATCHED = "watched"
    LIKED = "liked"
    WANT_TO_WATCH = "want_to_watch"
    DROPPED = "dropped"


class UserMovieInteraction(Base):
    __tablename__ = "user_movie_interactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    status = Column(SQLAlchemyEnum(InteractionStatusEnum), nullable=False)
    user = relationship("User", back_populates="interactions")
    movie = relationship("Movie", back_populates="interactions")
