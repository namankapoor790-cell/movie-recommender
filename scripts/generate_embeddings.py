"""Generate sentence-transformer embeddings for movie overviews.

Reads movies from Supabase, generates embeddings using all-MiniLM-L6-v2,
and stores them in the movie_embeddings table. Idempotent — skips movies
that already have embeddings.
"""

import os
import sys
import time

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 256


def get_supabase() -> Client:
    """Return a Supabase client using service role key."""
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", ""),
    )


def get_movies_without_embeddings(sb: Client) -> list[dict]:
    """Fetch movies that don't have embeddings yet."""
    # Get IDs that already have embeddings
    existing = sb.table("movie_embeddings").select("movie_id").execute()
    existing_ids = {r["movie_id"] for r in existing.data} if existing.data else set()

    # Fetch all movies with their overviews
    movies: list[dict] = []
    page_size = 1000
    offset = 0
    while True:
        result = (
            sb.table("movies")
            .select("id,title,overview,genres,language")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        if not result.data:
            break
        for m in result.data:
            if m["id"] not in existing_ids:
                movies.append(m)
        offset += page_size
        if len(result.data) < page_size:
            break

    return movies


def build_embedding_text(movie: dict) -> str:
    """Build the text string to embed for a movie.

    Combines title, genres, language, and overview for richer embeddings.
    """
    genres = ", ".join(movie.get("genres", []))
    parts = [
        movie.get("title", ""),
        f"Genres: {genres}" if genres else "",
        f"Language: {movie.get('language', '')}",
        movie.get("overview", ""),
    ]
    return " | ".join(p for p in parts if p)


def store_embeddings(sb: Client, records: list[dict]) -> int:
    """Store embedding records in Supabase. Returns count stored."""
    if not records:
        return 0
    result = sb.table("movie_embeddings").upsert(
        records,
        on_conflict="movie_id,model_name",
    ).execute()
    return len(result.data) if result.data else 0


def main() -> None:
    """Run the embedding generation pipeline."""
    sb = get_supabase()
    start = time.time()

    print("Loading sentence-transformer model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Model loaded: {MODEL_NAME}")

    print("\nFetching movies without embeddings...")
    movies = get_movies_without_embeddings(sb)
    print(f"Found {len(movies)} movies to embed")

    if not movies:
        print("Nothing to do!")
        return

    # Build texts
    texts = [build_embedding_text(m) for m in movies]

    # Generate embeddings in batches
    total_stored = 0
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_movies = movies[i : i + BATCH_SIZE]

        print(f"\nBatch {i // BATCH_SIZE + 1}: encoding {len(batch_texts)} movies...")
        embeddings = model.encode(batch_texts, show_progress_bar=True)

        records = [
            {
                "movie_id": movie["id"],
                "embedding": embedding.tolist(),
                "model_name": MODEL_NAME,
            }
            for movie, embedding in zip(batch_movies, embeddings)
        ]

        count = store_embeddings(sb, records)
        total_stored += count
        print(f"  Stored {count} embeddings ({total_stored}/{len(movies)} total)")

    elapsed = time.time() - start
    print(f"\nDone! {total_stored} embeddings generated in {elapsed / 60:.1f} minutes")


if __name__ == "__main__":
    main()
