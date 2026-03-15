# Movie Recommendation App — Project Plan

## Vision
A fast, beautiful app where users input any movie and get ranked similar movies with a similarity score and reasons for similarity. India-first: supports Bollywood, Tamil, Telugu, Malayalam, Kannada cinema.

## Target User
Movie lovers who are done watching a great film and want 5 more exactly like it. Primarily Indian users on OTT platforms.

## Similarity Methods (in order of implementation)
- [x] Method 1: Genre + metadata matching
- [ ] Method 2: Cast & crew overlap
- [ ] Method 3: Plot embedding similarity (sentence-transformers)
- [ ] Method 4: Mood/tone matching
- [ ] Method 5: Hybrid ensemble (combine all above)

## Phases

### Phase 1 — Setup ✅
- [x] Scaffold folder structure (frontend + backend + scripts)
- [x] Create Supabase schema (movies, movie_embeddings, movie_metadata)
- [x] Set up environment variables across all services
- [ ] Verify all API keys work

### Phase 2 — Data Pipeline ✅
- [x] TMDB fetch script — top 10,000 popular movies
- [x] TMDB fetch script — Indian regional cinema (Hindi, Tamil, Telugu, Malayalam, Kannada)
- [x] Store movies + metadata in Supabase
- [x] Generate embeddings with sentence-transformers
- [x] Store embeddings in pgvector

### Phase 3 — Backend API ✅
- [x] GET /health
- [x] GET /search?q= (movie autocomplete)
- [x] POST /recommend (core similarity engine)
- [x] GET /movie/:id (full movie details)
- [x] In-memory caching for repeat requests
- [x] Similarity reasons logic (same director, genre, themes etc.)

### Phase 4 — Frontend ✅
- [x] Home page with search bar + autocomplete
- [x] Results page with movie grid
- [x] MovieCard with similarity score ring
- [x] Language filter bar (All, English, Hindi, Tamil, etc.)
- [x] Loading and error states
- [x] Mobile responsive layout

### Phase 5 — Integration ✅
- [x] Connect frontend to backend
- [x] End-to-end test: search → select → results
- [x] Fix CORS issues
- [ ] Test on mobile (manual — open localhost:5173 on phone)

### Phase 6 — Deploy ⬜
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Set all environment variables on both platforms
- [ ] Smoke test on live URLs
- [ ] Share live link

## Current Sprint
> Update this section every session so Claude knows what you're working on.

**Working on:** Phase 6 — Deploy (Vercel + Render)
**Last completed:** Phase 5 — all integration tests passing
**Blocked by:** Nothing

## Known Issues / Bugs
> Add bugs here as you find them so Claude can track and fix them.

None yet.

## Database Schema Version
Current: v1 (initial)
Last migration: Phase 1 — created movies, movie_embeddings, movie_metadata tables

## Environment Variables Needed
### Backend (/backend/.env)
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_SERVICE_KEY
- TMDB_API_KEY
- TMDB_BASE_URL
- CORS_ORIGINS

### Frontend (/frontend/.env)
- VITE_API_URL
- VITE_APP_NAME

## Movie Data Stats
> Update these after running the data pipeline.

- Total movies in DB: 25,403
- Movies with embeddings: 25,403
- Movies with metadata: 1,507
- Languages covered: en, hi, ta, te, ml, kn + others
- Last pipeline run: 2026-03-15

## Deployment URLs
- Frontend (Vercel): Not deployed yet
- Backend (Render): Not deployed yet
- Supabase project: Not linked yet
