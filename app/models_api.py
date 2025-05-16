from typing import List, Optional
from pydantic import BaseModel, Field
from .models_db import InteractionStatusEnum


class UserBaseAPI(BaseModel):
    username: str
    email: Optional[str] = None


class UserCreateAPI(UserBaseAPI):
    pass


class UserAPI(UserBaseAPI):
    id: int

    class Config:
        from_attributes = True


class MovieBaseAPI(BaseModel):
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    rating_imdb: Optional[float] = None


class MovieCreateAPI(MovieBaseAPI):
    pass


class MovieAPI(MovieBaseAPI):
    id: int

    class Config:
        from_attributes = True


class UserMovieInteractionBaseAPI(BaseModel):
    movie_id: int
    status: InteractionStatusEnum


class UserMovieInteractionCreateAPI(UserMovieInteractionBaseAPI):
    pass


class UserMovieInteractionAPI(UserMovieInteractionBaseAPI):
    id: int
    user_id: int

    class Config:
        from_attributes = True
