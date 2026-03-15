-- Cosine similarity search function for movie recommendations
-- Run this in Supabase SQL Editor

CREATE OR REPLACE FUNCTION match_movies(
    query_embedding VECTOR(384),
    match_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.0
)
RETURNS TABLE(
    movie_id BIGINT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        me.movie_id,
        (1 - (me.embedding <=> query_embedding))::FLOAT AS similarity
    FROM movie_embeddings me
    WHERE (1 - (me.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY me.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
