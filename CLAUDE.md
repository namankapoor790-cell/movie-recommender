# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Movie recommendation app — input a movie, get similar movies with similarity scores (0–100%). Built for the Indian market with Bollywood and regional cinema support.

## Tech Stack
- **Frontend:** React + Tailwind CSS (Vite) at `/frontend`
- **Backend:** FastAPI (Python) at `/backend`
- **Database:** Supabase (PostgreSQL + pgvector)
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2, runs locally)
- **Movie Data:** TMDB API
- **Hosting:** Vercel (frontend) + Render (backend)

## Project Structure
```
/frontend       → React Vite app
/backend        → FastAPI Python app
/scripts        → One-time data pipeline scripts
PLAN.md         → Full project plan and progress tracker
```

## Commands
```bash
# Backend
cd backend && source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Verify setup
cd scripts && python verify_setup.py
```

## Code Style
- Python: async/await throughout, type hints on all functions, short docstring on every function
- React: functional components only, no class components
- Tailwind classes only — no inline styles
- All secrets via environment variables, never hardcoded
- Keep files under 300 lines — split if longer

## Environment Variables
- Never commit `.env` files; keep `.env.example` files up to date
- Backend: `/backend/.env` — Frontend: `/frontend/.env`

## Architecture Rules
- All DB operations go in `/backend/db.py`, not in route handlers
- Use Supabase client methods or parameterized queries — never raw SQL strings
- Check if a record exists before inserting (idempotent scripts)
- All API calls must have try/catch with meaningful error messages
- Backend endpoints return proper HTTP status codes
- Frontend shows user-friendly error states, never raw errors

## Constraints
- No Redux — use React state + Context only
- No paid APIs or services
- No heavy ML libraries beyond sentence-transformers
- Do not modify the SQL schema without noting it in PLAN.md

## Workflow
1. Update PLAN.md to mark feature in progress
2. Write backend endpoint first, test with curl
3. Build frontend component
4. Update PLAN.md to mark done
5. Check PLAN.md → "Current Sprint" for priorities
