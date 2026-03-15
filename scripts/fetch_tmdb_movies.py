"""Fetch movies from TMDB API and store in Supabase.

Fetches top popular movies globally + Indian regional cinema
(Hindi, Tamil, Telugu, Malayalam, Kannada). Idempotent — safe to re-run.
"""

import asyncio
import os
import sys
import time

import certifi
import httpx
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

# TMDB genre ID mapping
GENRE_MAP: dict[int, str] = {}

# Languages to fetch for Indian regional cinema
INDIAN_LANGUAGES: list[dict[str, str]] = [
    {"code": "hi", "name": "Hindi"},
    {"code": "ta", "name": "Tamil"},
    {"code": "te", "name": "Telugu"},
    {"code": "ml", "name": "Malayalam"},
    {"code": "kn", "name": "Kannada"},
]

# How many pages to fetch per category (20 movies per page)
POPULAR_PAGES = 500        # ~10,000 popular movies globally
HOLLYWOOD_PAGES = 500      # ~10,000 English-language movies via discover
TOP_RATED_PAGES = 200      # ~4,000 top-rated movies (mostly Hollywood)
REGIONAL_PAGES = 100       # ~2,000 per language = ~10,000 regional


def get_supabase() -> Client:
    """Return a Supabase client using service role key."""
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )


async def fetch_genre_map(client: httpx.AsyncClient, api_key: str, base_url: str) -> None:
    """Fetch TMDB genre ID → name mapping."""
    global GENRE_MAP
    resp = await client.get(
        f"{base_url}/genre/movie/list",
        params={"api_key": api_key},
    )
    resp.raise_for_status()
    GENRE_MAP = {g["id"]: g["name"] for g in resp.json()["genres"]}
    print(f"Loaded {len(GENRE_MAP)} genres")


def parse_movie(movie: dict) -> dict:
    """Parse a TMDB movie response into our schema."""
    genre_names = [GENRE_MAP.get(gid, "Unknown") for gid in movie.get("genre_ids", [])]
    return {
        "tmdb_id": movie["id"],
        "title": movie.get("title", ""),
        "original_title": movie.get("original_title", ""),
        "language": movie.get("original_language", "en"),
        "genres": genre_names,
        "overview": movie.get("overview", ""),
        "release_date": movie.get("release_date") or None,
        "poster_path": movie.get("poster_path"),
        "vote_average": movie.get("vote_average", 0),
        "vote_count": movie.get("vote_count", 0),
        "popularity": movie.get("popularity", 0),
    }


async def fetch_movies_page(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    endpoint: str,
    params: dict,
    page: int,
) -> list[dict]:
    """Fetch a single page of movies from TMDB."""
    params = {**params, "api_key": api_key, "page": page}
    resp = await client.get(f"{base_url}{endpoint}", params=params)
    if resp.status_code == 429:
        # Rate limited — wait and retry
        retry_after = int(resp.headers.get("Retry-After", "2"))
        print(f"  Rate limited, waiting {retry_after}s...")
        await asyncio.sleep(retry_after)
        return await fetch_movies_page(client, api_key, base_url, endpoint, params, page)
    resp.raise_for_status()
    return resp.json().get("results", [])


def upsert_movies(sb: Client, movies: list[dict]) -> int:
    """Insert movies into Supabase, skipping duplicates. Returns count inserted."""
    if not movies:
        return 0
    # Filter out movies with empty release_date strings
    for m in movies:
        if m["release_date"] == "":
            m["release_date"] = None
    result = sb.table("movies").upsert(
        movies,
        on_conflict="tmdb_id",
    ).execute()
    return len(result.data) if result.data else 0


async def fetch_popular_movies(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    sb: Client,
) -> int:
    """Fetch globally popular movies from TMDB."""
    total = 0
    print(f"\nFetching popular movies ({POPULAR_PAGES} pages)...")
    for page in range(1, POPULAR_PAGES + 1):
        try:
            raw = await fetch_movies_page(
                client, api_key, base_url,
                "/movie/popular",
                {"language": "en-US"},
                page,
            )
            movies = [parse_movie(m) for m in raw]
            count = upsert_movies(sb, movies)
            total += count
            if page % 50 == 0:
                print(f"  Page {page}/{POPULAR_PAGES} — {total} movies so far")
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            await asyncio.sleep(2)
    print(f"  Popular movies done: {total} total")
    return total


async def fetch_hollywood_movies(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    sb: Client,
) -> int:
    """Fetch English-language movies via TMDB discover endpoint."""
    total = 0
    print(f"\nFetching Hollywood/English movies ({HOLLYWOOD_PAGES} pages)...")
    for page in range(1, HOLLYWOOD_PAGES + 1):
        try:
            raw = await fetch_movies_page(
                client, api_key, base_url,
                "/discover/movie",
                {
                    "with_original_language": "en",
                    "sort_by": "popularity.desc",
                },
                page,
            )
            if not raw:
                print(f"  Hollywood: no more results at page {page}")
                break
            movies = [parse_movie(m) for m in raw]
            count = upsert_movies(sb, movies)
            total += count
            if page % 50 == 0:
                print(f"  Page {page}/{HOLLYWOOD_PAGES} — {total} Hollywood movies so far")
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            await asyncio.sleep(2)
    print(f"  Hollywood movies done: {total} total")
    return total


async def fetch_top_rated_movies(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    sb: Client,
) -> int:
    """Fetch top-rated movies from TMDB."""
    total = 0
    print(f"\nFetching top-rated movies ({TOP_RATED_PAGES} pages)...")
    for page in range(1, TOP_RATED_PAGES + 1):
        try:
            raw = await fetch_movies_page(
                client, api_key, base_url,
                "/movie/top_rated",
                {"language": "en-US"},
                page,
            )
            if not raw:
                print(f"  Top rated: no more results at page {page}")
                break
            movies = [parse_movie(m) for m in raw]
            count = upsert_movies(sb, movies)
            total += count
            if page % 50 == 0:
                print(f"  Page {page}/{TOP_RATED_PAGES} — {total} top-rated movies so far")
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            await asyncio.sleep(2)
    print(f"  Top-rated movies done: {total} total")
    return total


async def fetch_regional_movies(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    sb: Client,
) -> int:
    """Fetch Indian regional cinema from TMDB discover endpoint."""
    total = 0
    for lang in INDIAN_LANGUAGES:
        lang_total = 0
        print(f"\nFetching {lang['name']} movies ({REGIONAL_PAGES} pages)...")
        for page in range(1, REGIONAL_PAGES + 1):
            try:
                raw = await fetch_movies_page(
                    client, api_key, base_url,
                    "/discover/movie",
                    {
                        "with_original_language": lang["code"],
                        "sort_by": "popularity.desc",
                    },
                    page,
                )
                if not raw:
                    print(f"  {lang['name']}: no more results at page {page}")
                    break
                movies = [parse_movie(m) for m in raw]
                count = upsert_movies(sb, movies)
                lang_total += count
                if page % 50 == 0:
                    print(f"  Page {page}/{REGIONAL_PAGES} — {lang_total} {lang['name']} movies")
            except Exception as e:
                print(f"  Error on page {page}: {e}")
                await asyncio.sleep(2)
        print(f"  {lang['name']} done: {lang_total} movies")
        total += lang_total
    return total


async def fetch_metadata_for_movies(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    sb: Client,
) -> int:
    """Fetch cast/crew/keywords for movies that don't have metadata yet."""
    # Get movie IDs that lack metadata
    existing = sb.table("movie_metadata").select("movie_id").execute()
    existing_ids = {r["movie_id"] for r in existing.data} if existing.data else set()

    all_movies = sb.table("movies").select("id,tmdb_id").execute()
    to_fetch = [m for m in (all_movies.data or []) if m["id"] not in existing_ids]

    print(f"\nFetching metadata for {len(to_fetch)} movies...")
    total = 0
    for i, movie in enumerate(to_fetch):
        try:
            # Fetch credits
            credits_resp = await client.get(
                f"{base_url}/movie/{movie['tmdb_id']}/credits",
                params={"api_key": api_key},
            )
            if credits_resp.status_code == 429:
                retry_after = int(credits_resp.headers.get("Retry-After", "2"))
                await asyncio.sleep(retry_after)
                credits_resp = await client.get(
                    f"{base_url}/movie/{movie['tmdb_id']}/credits",
                    params={"api_key": api_key},
                )
            credits = credits_resp.json() if credits_resp.status_code == 200 else {}

            # Fetch keywords
            kw_resp = await client.get(
                f"{base_url}/movie/{movie['tmdb_id']}/keywords",
                params={"api_key": api_key},
            )
            if kw_resp.status_code == 429:
                retry_after = int(kw_resp.headers.get("Retry-After", "2"))
                await asyncio.sleep(retry_after)
                kw_resp = await client.get(
                    f"{base_url}/movie/{movie['tmdb_id']}/keywords",
                    params={"api_key": api_key},
                )
            keywords = kw_resp.json() if kw_resp.status_code == 200 else {}

            # Fetch movie details for runtime/budget/revenue/tagline
            details_resp = await client.get(
                f"{base_url}/movie/{movie['tmdb_id']}",
                params={"api_key": api_key},
            )
            details = details_resp.json() if details_resp.status_code == 200 else {}

            # Extract director
            crew = credits.get("crew", [])
            director = next((c["name"] for c in crew if c.get("job") == "Director"), None)

            # Build top 10 cast
            cast_list = [
                {"name": c["name"], "character": c.get("character", ""), "order": c.get("order", 0)}
                for c in credits.get("cast", [])[:10]
            ]

            metadata = {
                "movie_id": movie["id"],
                "cast_members": cast_list,
                "crew_members": [{"name": c["name"], "job": c["job"]} for c in crew[:10]],
                "keywords": [k["name"] for k in keywords.get("keywords", [])],
                "director": director,
                "budget": details.get("budget"),
                "revenue": details.get("revenue"),
                "runtime": details.get("runtime"),
                "tagline": details.get("tagline"),
            }

            sb.table("movie_metadata").upsert(
                metadata,
                on_conflict="movie_id",
            ).execute()
            total += 1

            if (i + 1) % 100 == 0:
                print(f"  Metadata: {i + 1}/{len(to_fetch)} done")

        except Exception as e:
            print(f"  Error fetching metadata for tmdb_id={movie['tmdb_id']}: {e}")
            await asyncio.sleep(1)

    print(f"  Metadata done: {total} movies")
    return total


async def main() -> None:
    """Run the full TMDB fetch pipeline."""
    api_key = os.getenv("TMDB_API_KEY", "")
    base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    sb = get_supabase()

    start = time.time()

    async with httpx.AsyncClient(timeout=30.0, verify=certifi.where()) as client:
        await fetch_genre_map(client, api_key, base_url)

        popular_count = await fetch_popular_movies(client, api_key, base_url, sb)
        hollywood_count = await fetch_hollywood_movies(client, api_key, base_url, sb)
        top_rated_count = await fetch_top_rated_movies(client, api_key, base_url, sb)
        regional_count = await fetch_regional_movies(client, api_key, base_url, sb)

        total_movies = popular_count + hollywood_count + top_rated_count + regional_count
        print(f"\n--- Movies fetched: {popular_count} popular + {hollywood_count} Hollywood + {top_rated_count} top-rated + {regional_count} regional = {total_movies} total ---")

        metadata_count = await fetch_metadata_for_movies(client, api_key, base_url, sb)
        print(f"--- Metadata fetched for {metadata_count} movies ---")

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed / 60:.1f} minutes")


if __name__ == "__main__":
    asyncio.run(main())
