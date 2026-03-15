import { useState } from 'react'
import SearchBar from './components/SearchBar'
import MovieCard from './components/MovieCard'
import LanguageFilter from './components/LanguageFilter'
import { getRecommendations, getMovieDetail, posterUrl } from './api'

function App() {
  const [sourceMovie, setSourceMovie] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [languageFilter, setLanguageFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleMovieSelect(movie) {
    setLoading(true)
    setError(null)
    setRecommendations([])
    setSourceMovie(movie)
    setLanguageFilter('all')

    try {
      const data = await getRecommendations(movie.id, 20)
      setRecommendations(data.recommendations)
    } catch {
      setError('Could not find recommendations. Please try another movie.')
    } finally {
      setLoading(false)
    }
  }

  async function handleCardClick(movie) {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    handleMovieSelect(movie)
  }

  const filtered =
    languageFilter === 'all'
      ? recommendations
      : recommendations.filter((m) => m.language === languageFilter)

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-gray-900/95 backdrop-blur border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center gap-4">
          <h1
            className="text-xl font-bold text-purple-400 cursor-pointer flex-shrink-0"
            onClick={() => {
              setSourceMovie(null)
              setRecommendations([])
              setError(null)
            }}
          >
            Endless Eden
          </h1>
          <SearchBar onSelect={handleMovieSelect} />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Landing state */}
        {!sourceMovie && !loading && (
          <div className="text-center mt-24">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              Find movies you'll <span className="text-purple-400">love</span>
            </h2>
            <p className="text-gray-400 text-lg max-w-md mx-auto">
              Search for any movie and we'll find similar ones with similarity scores and reasons.
            </p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center mt-24 gap-4">
            <div className="w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400">Finding similar movies...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center mt-24">
            <p className="text-red-400 text-lg">{error}</p>
          </div>
        )}

        {/* Results */}
        {sourceMovie && recommendations.length > 0 && !loading && (
          <>
            {/* Source movie banner */}
            <div className="flex items-center gap-4 mb-8 p-4 bg-gray-800 rounded-xl">
              {posterUrl(sourceMovie.poster_path, 'w154') ? (
                <img
                  src={posterUrl(sourceMovie.poster_path, 'w154')}
                  alt=""
                  className="w-16 h-24 rounded-lg object-cover flex-shrink-0"
                />
              ) : (
                <div className="w-16 h-24 rounded-lg bg-gray-700 flex-shrink-0" />
              )}
              <div>
                <p className="text-gray-400 text-sm">Movies similar to</p>
                <h2 className="text-2xl font-bold">{sourceMovie.title}</h2>
                <p className="text-gray-400 text-sm mt-1">
                  {sourceMovie.release_date?.slice(0, 4)} · {sourceMovie.genres?.slice(0, 3).join(', ')}
                </p>
              </div>
              <span className="ml-auto text-yellow-400 font-medium text-lg flex-shrink-0">
                ★ {sourceMovie.vote_average?.toFixed(1)}
              </span>
            </div>

            {/* Language filter */}
            <div className="mb-6">
              <LanguageFilter selected={languageFilter} onChange={setLanguageFilter} />
            </div>

            {/* Results count */}
            <p className="text-gray-400 text-sm mb-4">
              {filtered.length} recommendation{filtered.length !== 1 ? 's' : ''} found
            </p>

            {/* Movie grid */}
            {filtered.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {filtered.map((movie) => (
                  <MovieCard key={movie.id} movie={movie} onClick={handleCardClick} />
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 mt-12">
                No recommendations for this language filter.
              </p>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
