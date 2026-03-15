"""Pydantic models for API request/response shapes."""

from pydantic import BaseModel
from datetime import date


class MovieBase(BaseModel):
    """Core movie fields from TMDB."""
    tmdb_id: int
    title: str
    original_title: str
    language: str
    genres: list[str]
    overview: str
    release_date: date | None
    poster_path: str | None
    vote_average: float
    vote_count: int
    popularity: float


class MovieSearchResult(BaseModel):
    """Movie result for autocomplete search."""
    id: int
    tmdb_id: int
    title: str
    original_title: str
    language: str
    genres: list[str]
    poster_path: str | None
    release_date: date | None
    vote_average: float


class MovieDetail(BaseModel):
    """Full movie details including metadata."""
    id: int
    tmdb_id: int
    title: str
    original_title: str
    language: str
    genres: list[str]
    overview: str
    release_date: date | None
    poster_path: str | None
    vote_average: float
    vote_count: int
    popularity: float
    director: str | None = None
    cast_members: list[dict] | None = None
    keywords: list[str] | None = None


class RecommendRequest(BaseModel):
    """Request body for movie recommendations."""
    movie_id: int
    limit: int = 10


class SimilarityReason(BaseModel):
    """Explains why a movie was recommended."""
    reason: str
    detail: str


class RecommendedMovie(BaseModel):
    """A single recommendation with score and reasons."""
    id: int
    tmdb_id: int
    title: str
    original_title: str
    language: str
    genres: list[str]
    overview: str
    poster_path: str | None
    release_date: date | None
    vote_average: float
    similarity_score: int  # 0-100
    reasons: list[SimilarityReason]


class RecommendResponse(BaseModel):
    """Response from the recommend endpoint."""
    source_movie: MovieSearchResult
    recommendations: list[RecommendedMovie]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
