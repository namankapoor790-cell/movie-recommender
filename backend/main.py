"""FastAPI application entry point for the Movie Recommender API."""

import os
from datetime import datetime, timezone
from functools import lru_cache

import certifi
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import (
    find_similar_by_embedding,
    get_metadata_by_movie_ids,
    get_movie_by_id,
    get_movie_embedding,
    get_movie_metadata,
    get_movies_by_ids,
    search_movies,
    test_connection,
)
from models import (
    MovieDetail,
    MovieSearchResult,
    RecommendedMovie,
    RecommendRequest,
    RecommendResponse,
)
from recommender import compute_reasons

load_dotenv()

app = FastAPI(title="Movie Recommender API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory cache for recommendations
_recommend_cache: dict[str, dict] = {}
MAX_CACHE_SIZE = 500


# --- Health endpoints ---

@app.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/health/supabase")
async def health_supabase() -> dict:
    """Verify Supabase connection."""
    connected = await test_connection()
    return {"status": "ok" if connected else "error", "service": "supabase"}


@app.get("/health/tmdb")
async def health_tmdb() -> dict:
    """Verify TMDB API key works."""
    api_key = os.getenv("TMDB_API_KEY", "")
    base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    try:
        async with httpx.AsyncClient(verify=certifi.where()) as client:
            resp = await client.get(
                f"{base_url}/configuration",
                params={"api_key": api_key},
            )
            return {
                "status": "ok" if resp.status_code == 200 else "error",
                "service": "tmdb",
                "http_status": resp.status_code,
            }
    except Exception as e:
        return {"status": "error", "service": "tmdb", "detail": str(e)}


# --- Search endpoint ---

@app.get("/search", response_model=list[MovieSearchResult])
async def search(q: str = Query(..., min_length=1, description="Search query")) -> list[dict]:
    """Search movies by title with autocomplete."""
    results = await search_movies(q, limit=10)
    return results


# --- Movie detail endpoint ---

@app.get("/movie/{movie_id}", response_model=MovieDetail)
async def get_movie(movie_id: int) -> dict:
    """Get full movie details including metadata."""
    movie = await get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    metadata = await get_movie_metadata(movie_id)
    if metadata:
        movie["director"] = metadata.get("director")
        movie["cast_members"] = metadata.get("cast_members")
        movie["keywords"] = metadata.get("keywords")

    return movie


# --- Recommendation endpoint ---

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest) -> dict:
    """Get movie recommendations based on similarity."""
    # Check cache
    cache_key = f"{req.movie_id}:{req.limit}"
    if cache_key in _recommend_cache:
        return _recommend_cache[cache_key]

    # Get source movie
    source = await get_movie_by_id(req.movie_id)
    if not source:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Get source embedding
    embedding = await get_movie_embedding(req.movie_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="No embedding found for this movie")

    # Find similar movies by embedding
    similar = await find_similar_by_embedding(embedding, req.movie_id, req.limit)
    if not similar:
        raise HTTPException(status_code=404, detail="No similar movies found")

    # Fetch full movie data for all matches
    match_ids = [m["movie_id"] for m in similar]
    similarity_map = {m["movie_id"]: m["similarity"] for m in similar}

    movies = await get_movies_by_ids(match_ids)
    movie_map = {m["id"]: m for m in movies}

    # Fetch metadata for source + all matches
    all_ids = [req.movie_id] + match_ids
    metadata_map = await get_metadata_by_movie_ids(all_ids)
    source_meta = metadata_map.get(req.movie_id)

    # Build recommendations with reasons
    recommendations = []
    for match_id in match_ids:
        movie = movie_map.get(match_id)
        if not movie:
            continue

        sim_score = similarity_map.get(match_id, 0)
        score_pct = max(0, min(100, int(sim_score * 100)))

        candidate_meta = metadata_map.get(match_id)
        reasons = compute_reasons(source, movie, source_meta, candidate_meta)

        recommendations.append(RecommendedMovie(
            id=movie["id"],
            tmdb_id=movie["tmdb_id"],
            title=movie["title"],
            original_title=movie["original_title"],
            language=movie["language"],
            genres=movie["genres"],
            overview=movie["overview"],
            poster_path=movie.get("poster_path"),
            release_date=movie.get("release_date"),
            vote_average=movie["vote_average"],
            similarity_score=score_pct,
            reasons=reasons,
        ))

    # Sort by similarity score descending
    recommendations.sort(key=lambda r: r.similarity_score, reverse=True)

    source_result = MovieSearchResult(
        id=source["id"],
        tmdb_id=source["tmdb_id"],
        title=source["title"],
        original_title=source["original_title"],
        language=source["language"],
        genres=source["genres"],
        poster_path=source.get("poster_path"),
        release_date=source.get("release_date"),
        vote_average=source["vote_average"],
    )

    response = RecommendResponse(
        source_movie=source_result,
        recommendations=recommendations,
    )

    # Cache result
    if len(_recommend_cache) >= MAX_CACHE_SIZE:
        _recommend_cache.clear()
    _recommend_cache[cache_key] = response.model_dump()

    return response
