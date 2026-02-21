/**
 * useMovieRecognition Hook
 * React hook for movie recognition via TMDB
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { MovieRecognitionResponse, Movie } from '../types/api';

export interface MovieRecognitionState {
  movie: Movie | null;
  isRecognizing: boolean;
  error: string | null;
}

export function useMovieRecognition() {
  const [state, setState] = useState<MovieRecognitionState>({
    movie: null,
    isRecognizing: false,
    error: null,
  });

  /**
   * Recognize movie from filename
   */
  const recognizeMovie = useCallback(
    async (filename: string, imdbId?: string) => {
      setState((prev) => ({ ...prev, isRecognizing: true, error: null }));

      try {
        const response = await api.recognizeMovie(filename, imdbId);

        if (response.success && response.movie) {
          setState({
            movie: response.movie,
            isRecognizing: false,
            error: null,
          });
          return response.movie;
        } else {
          setState({
            movie: null,
            isRecognizing: false,
            error: response.message || 'Movie not found',
          });
          return null;
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Movie recognition failed';
        setState({
          movie: null,
          isRecognizing: false,
          error: errorMessage,
        });
        return null;
      }
    },
    []
  );

  /**
   * Recognize movie from File object
   */
  const recognizeMovieFromFile = useCallback(
    async (file: File, imdbId?: string) => {
      return recognizeMovie(file.name, imdbId);
    },
    [recognizeMovie]
  );

  /**
   * Set movie manually
   */
  const setMovie = useCallback((movie: Movie | null) => {
    setState((prev) => ({
      ...prev,
      movie,
      error: null,
    }));
  }, []);

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  /**
   * Reset state
   */
  const reset = useCallback(() => {
    setState({
      movie: null,
      isRecognizing: false,
      error: null,
    });
  }, []);

  return {
    // State
    ...state,

    // Actions
    recognizeMovie,
    recognizeMovieFromFile,
    setMovie,
    clearError,
    reset,
  };
}
