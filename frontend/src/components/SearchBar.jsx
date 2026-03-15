import { useState, useEffect, useRef } from 'react'
import { searchMovies, posterUrl } from '../api'

export default function SearchBar({ onSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)
  const wrapperRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (query.length < 2) {
      setResults([])
      setIsOpen(false)
      return
    }

    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await searchMovies(query)
        setResults(data)
        setIsOpen(true)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => clearTimeout(debounceRef.current)
  }, [query])

  function handleSelect(movie) {
    setQuery(movie.title)
    setIsOpen(false)
    setResults([])
    onSelect(movie)
  }

  return (
    <div ref={wrapperRef} className="relative w-full max-w-xl mx-auto">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for a movie..."
          className="w-full px-5 py-4 bg-gray-800 border border-gray-700 rounded-xl text-white text-lg placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors"
        />
        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <ul className="absolute z-50 w-full mt-2 bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-2xl max-h-96 overflow-y-auto">
          {results.map((movie) => (
            <li
              key={movie.id}
              onClick={() => handleSelect(movie)}
              className="flex items-center gap-3 px-4 py-3 hover:bg-gray-700 cursor-pointer transition-colors"
            >
              {posterUrl(movie.poster_path, 'w92') ? (
                <img
                  src={posterUrl(movie.poster_path, 'w92')}
                  alt=""
                  className="w-10 h-14 rounded object-cover flex-shrink-0"
                />
              ) : (
                <div className="w-10 h-14 rounded bg-gray-700 flex-shrink-0" />
              )}
              <div className="min-w-0">
                <p className="text-white font-medium truncate">{movie.title}</p>
                <p className="text-gray-400 text-sm">
                  {movie.release_date?.slice(0, 4)} · {movie.genres?.slice(0, 2).join(', ')}
                </p>
              </div>
              <span className="ml-auto text-yellow-400 text-sm flex-shrink-0">
                ★ {movie.vote_average?.toFixed(1)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
