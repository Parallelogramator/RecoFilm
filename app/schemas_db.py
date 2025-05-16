from typing import List, Optional
from pydantic import BaseModel, Field
from .models_db import InteractionStatusEnum


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserCore(UserBase):
    id: int

    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    rating_imdb: Optional[float] = None


class MovieCreate(MovieBase):
    pass


class MovieCore(MovieBase):
    id: int

    class Config:
        from_attributes = True


class UserMovieInteractionBase(BaseModel):
    movie_id: int
    status: InteractionStatusEnum


class UserMovieInteractionCreate(UserMovieInteractionBase):
    pass


class UserMovieInteractionCore(UserMovieInteractionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
