# Pydantic модели или dataclasses
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, Index
from sqlalchemy.orm import relationship
from .database import Base
import enum

class WatchStatusEnum(enum.Enum):
    watched = "просмотрено"
    planned = "запланировано"
    dropped = "брошено"
    watching = "смотрю"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    movies = relationship("UserMovie", back_populates="user")

class AllMovie(Base):
    __tablename__ = "all_movies"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    genres = Column(String)

    __table_args__ = (
        Index('idx_all_movies_id', 'id'),
        Index('idx_all_movies_genres', 'genres'),
    )

class UserMovie(Base):
    __tablename__ = "user_movies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("all_movies.id"))
    status = Column(Enum(WatchStatusEnum))
    rate = Column(Float)

    user = relationship("User", back_populates="movies")
    movie = relationship("AllMovie")