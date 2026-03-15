-- Movie Recommendation App — Database Schema v1
-- Run this in Supabase SQL Editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Core movie data from TMDB
CREATE TABLE movies (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tmdb_id INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    original_title TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    genres TEXT[] NOT NULL DEFAULT '{}',
    overview TEXT NOT NULL DEFAULT '',
    release_date DATE,
    poster_path TEXT,
    vote_average REAL NOT NULL DEFAULT 0,
    vote_count INTEGER NOT NULL DEFAULT 0,
    popularity REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_movies_tmdb_id ON movies(tmdb_id);
CREATE INDEX idx_movies_language ON movies(language);
CREATE INDEX idx_movies_popularity ON movies(popularity DESC);

-- Sentence-transformer embeddings (384 dimensions for all-MiniLM-L6-v2)
CREATE TABLE movie_embeddings (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    movie_id BIGINT NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    embedding VECTOR(384) NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(movie_id, model_name)
);

CREATE INDEX idx_embeddings_movie_id ON movie_embeddings(movie_id);

-- Extended metadata: cast, crew, keywords
CREATE TABLE movie_metadata (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    movie_id BIGINT NOT NULL REFERENCES movies(id) ON DELETE CASCADE UNIQUE,
    cast_members JSONB NOT NULL DEFAULT '[]',
    crew_members JSONB NOT NULL DEFAULT '[]',
    keywords TEXT[] NOT NULL DEFAULT '{}',
    director TEXT,
    budget BIGINT,
    revenue BIGINT,
    runtime INTEGER,
    tagline TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metadata_movie_id ON movie_metadata(movie_id);
CREATE INDEX idx_metadata_director ON movie_metadata(director);

-- Row Level Security: public read, service role write
ALTER TABLE movies ENABLE ROW LEVEL SECURITY;
ALTER TABLE movie_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE movie_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access" ON movies FOR SELECT USING (true);
CREATE POLICY "Public read access" ON movie_embeddings FOR SELECT USING (true);
CREATE POLICY "Public read access" ON movie_metadata FOR SELECT USING (true);

CREATE POLICY "Service insert" ON movies FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update" ON movies FOR UPDATE USING (true);
CREATE POLICY "Service insert" ON movie_embeddings FOR INSERT WITH CHECK (true);
CREATE POLICY "Service insert" ON movie_metadata FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update" ON movie_metadata FOR UPDATE USING (true);
