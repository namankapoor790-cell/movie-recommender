"""Verify all environment variables and API connections work."""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))


async def verify_all() -> None:
    """Run all verification checks."""
    print("Checking environment variables...")
    required = ["SUPABASE_URL", "SUPABASE_KEY", "TMDB_API_KEY"]
    all_ok = True
    for var in required:
        val = os.getenv(var)
        status = "OK" if val else "MISSING"
        if not val:
            all_ok = False
        print(f"  {status}: {var}")

    print("\nChecking TMDB API...")
    base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{base_url}/configuration",
                params={"api_key": os.getenv("TMDB_API_KEY", "")},
            )
            status = "OK" if resp.status_code == 200 else f"FAIL (HTTP {resp.status_code})"
            if resp.status_code != 200:
                all_ok = False
            print(f"  TMDB: {status}")
    except Exception as e:
        all_ok = False
        print(f"  TMDB: FAIL ({e})")

    print("\nChecking Supabase...")
    try:
        sb = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", ""),
        )
        sb.table("movies").select("id").limit(1).execute()
        print("  Supabase: OK")
    except Exception as e:
        all_ok = False
        print(f"  Supabase: FAIL ({e})")

    print(f"\n{'All checks passed!' if all_ok else 'Some checks failed.'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(verify_all())
