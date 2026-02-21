/**
 * MovieCard Component
 * Display movie information from TMDB
 */

import type { Movie } from '../types/api';
import { Card, CardContent } from './Card';

export interface MovieCardProps {
  movie: Movie;
  onSelect?: () => void;
}

export function MovieCard({ movie, onSelect }: MovieCardProps) {
  const { title, year, rating, poster, overview, imdb_id } = movie;

  return (
    <Card
      variant="elevated"
      padding="none"
      className="overflow-hidden hover:shadow-2xl hover:scale-[1.01] transition-all animate-fade-in"
      onClick={onSelect}
    >
      <div className="flex flex-col md:flex-row">
        {/* Poster */}
        <div className="md:w-56 flex-shrink-0 bg-slate-800 relative overflow-hidden">
          {poster ? (
            <img
              src={poster}
              alt={`${title} poster`}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-64 md:h-full flex items-center justify-center text-7xl bg-gradient-to-br from-slate-700 to-slate-800">
              🎬
            </div>
          )}
          {/* Overlay gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        </div>

        {/* Content */}
        <CardContent className="p-6 flex-1 bg-gradient-to-br from-slate-800/95 to-slate-900/95">
          {/* Title & Year */}
          <div className="mb-4">
            <h3 className="text-3xl font-black text-white mb-2 drop-shadow-lg">{title}</h3>
            <p className="text-base text-cyan-300 font-semibold">{year}</p>
          </div>

          {/* Rating */}
          {rating !== undefined && rating > 0 && (
            <div className="flex items-center gap-3 mb-4 bg-yellow-500/10 px-4 py-2 rounded-lg border border-yellow-500/30 w-fit">
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`w-6 h-6 ${
                      i < Math.round(rating / 2)
                        ? 'text-yellow-400'
                        : 'text-gray-600'
                    }`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              <span className="text-base font-bold text-yellow-300">{rating.toFixed(1)}/10</span>
            </div>
          )}

          {/* Overview */}
          {overview && (
            <p className="text-base text-gray-200 mb-5 line-clamp-4 leading-relaxed font-medium">{overview}</p>
          )}

          {/* IMDb Link */}
          {imdb_id && (
            <a
              href={`https://www.imdb.com/title/${imdb_id}/`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-base font-semibold text-cyan-300 hover:text-cyan-200 bg-cyan-500/10 px-4 py-2 rounded-lg border border-cyan-500/30 hover:border-cyan-400/50 transition-all"
              onClick={(e) => e.stopPropagation()}
            >
              <span>View on IMDb</span>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          )}
        </CardContent>
      </div>
    </Card>
  );
}
