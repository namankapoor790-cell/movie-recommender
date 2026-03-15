const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function searchMovies(query) {
  const res = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`)
  if (!res.ok) throw new Error('Search failed')
  return res.json()
}

export async function getRecommendations(movieId, limit = 10) {
  const res = await fetch(`${API_URL}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ movie_id: movieId, limit }),
  })
  if (!res.ok) throw new Error('Recommendations failed')
  return res.json()
}

export async function getMovieDetail(movieId) {
  const res = await fetch(`${API_URL}/movie/${movieId}`)
  if (!res.ok) throw new Error('Movie not found')
  return res.json()
}

export function posterUrl(path, size = 'w342') {
  if (!path) return null
  return `https://image.tmdb.org/t/p/${size}${path}`
}
