/**
 * useTranslation Hook
 * React hook for subtitle translation using Google Gemini
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';

export interface TranslationState {
  isTranslating: boolean;
  progress: number;
  error: string | null;
}

export interface TranslationOptions {
  sourceLang: string;
  targetLang: string;
  movieContext?: string;
}

export function useTranslation() {
  const [state, setState] = useState<TranslationState>({
    isTranslating: false,
    progress: 0,
    error: null,
  });

  /**
   * Translate subtitle file
   */
  const translateSubtitle = useCallback(
    async (
      subtitleFile: File,
      options: TranslationOptions
    ): Promise<Blob | null> => {
      setState({ isTranslating: true, progress: 0, error: null });

      try {
        // Simulate progress (since API doesn't provide progress updates)
        const progressInterval = setInterval(() => {
          setState((prev) => ({
            ...prev,
            progress: Math.min(prev.progress + 10, 90),
          }));
        }, 500);

        const blob = await api.translateSubtitle(
          subtitleFile,
          options.sourceLang,
          options.targetLang,
          options.movieContext
        );

        clearInterval(progressInterval);

        setState({
          isTranslating: false,
          progress: 100,
          error: null,
        });

        // Generate filename
        const originalName = subtitleFile.name.replace(/\.[^/.]+$/, '');
        const filename = `${originalName}_${options.targetLang}.srt`;
        api.downloadBlob(blob, filename);

        return blob;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Translation failed';
        setState({
          isTranslating: false,
          progress: 0,
          error: errorMessage,
        });
        return null;
      }
    },
    []
  );

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
      isTranslating: false,
      progress: 0,
      error: null,
    });
  }, []);

  return {
    // State
    ...state,

    // Actions
    translateSubtitle,
    clearError,
    reset,
  };
}
