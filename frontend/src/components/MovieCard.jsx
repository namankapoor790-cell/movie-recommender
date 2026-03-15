import { posterUrl } from '../api'

function ScoreRing({ score }) {
  const radius = 22
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  let color = 'text-red-500'
  if (score >= 70) color = 'text-green-400'
  else if (score >= 50) color = 'text-yellow-400'

  return (
    <div className="relative w-14 h-14 flex-shrink-0">
      <svg className="w-14 h-14 -rotate-90" viewBox="0 0 52 52">
        <circle
          cx="26" cy="26" r={radius}
          fill="rgba(0,0,0,0.7)"
          stroke="currentColor"
          strokeWidth="3"
          className="text-gray-700"
        />
        <circle
          cx="26" cy="26" r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={color}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-white text-sm font-bold">
        {score}%
      </span>
    </div>
  )
}

export default function MovieCard({ movie, onClick }) {
  const poster = posterUrl(movie.poster_path)
  const year = movie.release_date?.slice(0, 4)

  return (
    <div
      onClick={() => onClick?.(movie)}
      className="group bg-gray-800 rounded-xl overflow-hidden cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all hover:scale-[1.02]"
    >
      <div className="relative aspect-[2/3] bg-gray-700">
        {poster ? (
          <img src={poster} alt={movie.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500 text-sm px-4 text-center">
            {movie.title}
          </div>
        )}
        {movie.similarity_score !== undefined && (
          <div className="absolute top-2 right-2">
            <ScoreRing score={movie.similarity_score} />
          </div>
        )}
      </div>

      <div className="p-3">
        <h3 className="text-white font-semibold text-sm truncate">{movie.title}</h3>
        <p className="text-gray-400 text-xs mt-1">
          {year} · {movie.genres?.slice(0, 2).join(', ')}
        </p>

        {movie.reasons && movie.reasons.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {movie.reasons.slice(0, 2).map((r, i) => (
              <span
                key={i}
                className="inline-block px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full"
              >
                {r.reason}: {r.detail}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
