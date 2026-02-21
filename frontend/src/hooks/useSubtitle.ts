/**
 * useSubtitle Hook
 * React hook for subtitle file operations
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type {
  SubtitleSearchResponse,
  EmbeddedSubtitlesResponse,
  Subtitle,
} from '../types/api';

export interface SubtitleState {
  file: File | null;
  searchResults: Subtitle[];
  embeddedSubtitles: EmbeddedSubtitlesResponse | null;
  isSearching: boolean;
  isDownloading: boolean;
  isExtracting: boolean;
  error: string | null;
}

export function useSubtitle() {
  const [state, setState] = useState<SubtitleState>({
    file: null,
    searchResults: [],
    embeddedSubtitles: null,
    isSearching: false,
    isDownloading: false,
    isExtracting: false,
    error: null,
  });

  /**
   * Set subtitle file
   */
  const setSubtitleFile = useCallback((file: File | null) => {
    setState((prev) => ({
      ...prev,
      file,
      error: null,
    }));
  }, []);

  /**
   * Search subtitles on OpenSubtitles
   */
  const searchSubtitles = useCallback(
    async (query: string, language: string = 'pt', limit: number = 10) => {
      setState((prev) => ({ ...prev, isSearching: true, error: null }));

      try {
        const response = await api.searchSubtitles(query, language, limit);
        setState((prev) => ({
          ...prev,
          searchResults: response.subtitles,
          isSearching: false,
        }));
        return response;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Subtitle search failed';
        setState((prev) => ({
          ...prev,
          isSearching: false,
          error: errorMessage,
        }));
        return null;
      }
    },
    []
  );

  /**
   * Download subtitle from OpenSubtitles
   */
  const downloadSubtitle = useCallback(async (fileId: number, filename?: string) => {
    setState((prev) => ({ ...prev, isDownloading: true, error: null }));

    try {
      const blob = await api.downloadSubtitle(fileId);
      setState((prev) => ({ ...prev, isDownloading: false }));

      // Generate filename if not provided
      const finalFilename = filename || `subtitle_${fileId}.srt`;
      api.downloadBlob(blob, finalFilename);

      return blob;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Subtitle download failed';
      setState((prev) => ({
        ...prev,
        isDownloading: false,
        error: errorMessage,
      }));
      return null;
    }
  }, []);

  /**
   * Extract embedded subtitles from MKV
   */
  const extractMkvSubtitles = useCallback(async (videoFile: File) => {
    setState((prev) => ({ ...prev, isExtracting: true, error: null }));

    try {
      const response = await api.extractMkvSubtitles(videoFile);
      setState((prev) => ({
        ...prev,
        embeddedSubtitles: response,
        isExtracting: false,
      }));
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Subtitle extraction failed';
      setState((prev) => ({
        ...prev,
        isExtracting: false,
        error: errorMessage,
      }));
      return null;
    }
  }, []);

  /**
   * Download embedded subtitle (from base64)
   */
  const downloadEmbeddedSubtitle = useCallback((subtitle: any) => {
    try {
      // Decode base64
      const binaryString = atob(subtitle.content_base64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/x-subrip' });

      // Download
      api.downloadBlob(blob, subtitle.file_name);
      return blob;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to download embedded subtitle';
      setState((prev) => ({ ...prev, error: errorMessage }));
      return null;
    }
  }, []);

  /**
   * Clear search results
   */
  const clearSearchResults = useCallback(() => {
    setState((prev) => ({ ...prev, searchResults: [] }));
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
      file: null,
      searchResults: [],
      embeddedSubtitles: null,
      isSearching: false,
      isDownloading: false,
      isExtracting: false,
      error: null,
    });
  }, []);

  return {
    // State
    ...state,

    // Actions
    setSubtitleFile,
    searchSubtitles,
    downloadSubtitle,
    extractMkvSubtitles,
    downloadEmbeddedSubtitle,
    clearSearchResults,
    clearError,
    reset,
  };
}
