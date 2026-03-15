"""Database operations module. All Supabase interactions go through here."""

import os
from functools import lru_cache

from supabase import create_client, Client


_client: Client | None = None


def get_supabase_client() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", "")
        _client = create_client(url, key)
    return _client


async def test_connection() -> bool:
    """Test that the Supabase connection works."""
    try:
        client = get_supabase_client()
        client.table("movies").select("id").limit(1).execute()
        return True
    except Exception:
        return False


async def search_movies(query: str, limit: int = 10) -> list[dict]:
    """Search movies by title using ilike. Returns matching movies."""
    client = get_supabase_client()
    result = (
        client.table("movies")
        .select("id,tmdb_id,title,original_title,language,genres,poster_path,release_date,vote_average")
        .ilike("title", f"%{query}%")
        .order("popularity", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


async def get_movie_by_id(movie_id: int) -> dict | None:
    """Fetch a single movie by its internal ID."""
    client = get_supabase_client()
    result = (
        client.table("movies")
        .select("*")
        .eq("id", movie_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_movie_metadata(movie_id: int) -> dict | None:
    """Fetch metadata (cast, crew, keywords) for a movie."""
    client = get_supabase_client()
    result = (
        client.table("movie_metadata")
        .select("*")
        .eq("movie_id", movie_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_movie_embedding(movie_id: int) -> list[float] | None:
    """Fetch the embedding vector for a movie."""
    client = get_supabase_client()
    result = (
        client.table("movie_embeddings")
        .select("embedding")
        .eq("movie_id", movie_id)
        .limit(1)
        .execute()
    )
    if result.data and result.data[0].get("embedding"):
        return result.data[0]["embedding"]
    return None


async def find_similar_by_embedding(
    embedding: list[float],
    exclude_id: int,
    limit: int = 10,
) -> list[dict]:
    """Find similar movies using pgvector cosine similarity."""
    client = get_supabase_client()
    result = client.rpc(
        "match_movies",
        {
            "query_embedding": embedding,
            "match_count": limit + 1,
            "similarity_threshold": 0.0,
        },
    ).execute()

    # Exclude the source movie and cap at limit
    matches = [r for r in (result.data or []) if r["movie_id"] != exclude_id]
    return matches[:limit]


async def get_movies_by_ids(movie_ids: list[int]) -> list[dict]:
    """Fetch multiple movies by their IDs."""
    if not movie_ids:
        return []
    client = get_supabase_client()
    result = (
        client.table("movies")
        .select("id,tmdb_id,title,original_title,language,genres,overview,poster_path,release_date,vote_average,vote_count,popularity")
        .in_("id", movie_ids)
        .execute()
    )
    return result.data or []


async def get_metadata_by_movie_ids(movie_ids: list[int]) -> dict[int, dict]:
    """Fetch metadata for multiple movies. Returns dict keyed by movie_id."""
    if not movie_ids:
        return {}
    client = get_supabase_client()
    result = (
        client.table("movie_metadata")
        .select("movie_id,director,cast_members,keywords")
        .in_("movie_id", movie_ids)
        .execute()
    )
    return {r["movie_id"]: r for r in (result.data or [])}
