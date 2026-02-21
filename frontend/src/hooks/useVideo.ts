/**
 * useVideo Hook
 * React hook for video file operations
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { VideoAnalysisResponse } from '../types/api';

export interface VideoState {
  file: File | null;
  analysis: VideoAnalysisResponse | null;
  isAnalyzing: boolean;
  isConverting: boolean;
  isRemuxing: boolean;
  error: string | null;
}

export function useVideo() {
  const [state, setState] = useState<VideoState>({
    file: null,
    analysis: null,
    isAnalyzing: false,
    isConverting: false,
    isRemuxing: false,
    error: null,
  });

  /**
   * Set video file
   */
  const setVideoFile = useCallback((file: File | null) => {
    setState((prev) => ({
      ...prev,
      file,
      analysis: null,
      error: null,
    }));
  }, []);

  /**
   * Analyze video file
   */
  const analyzeVideo = useCallback(async (file?: File) => {
    const videoFile = file || state.file;
    if (!videoFile) {
      setState((prev) => ({ ...prev, error: 'No video file selected' }));
      return null;
    }

    setState((prev) => ({ ...prev, isAnalyzing: true, error: null }));

    try {
      const analysis = await api.analyzeVideo(videoFile);
      setState((prev) => ({
        ...prev,
        analysis,
        isAnalyzing: false,
      }));
      return analysis;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Video analysis failed';
      setState((prev) => ({
        ...prev,
        isAnalyzing: false,
        error: errorMessage,
      }));
      return null;
    }
  }, [state.file]);

  /**
   * Remux MKV to MP4 (fast, no re-encoding)
   */
  const remuxMkvToMp4 = useCallback(async (file?: File) => {
    const videoFile = file || state.file;
    if (!videoFile) {
      setState((prev) => ({ ...prev, error: 'No video file selected' }));
      return null;
    }

    setState((prev) => ({ ...prev, isRemuxing: true, error: null }));

    try {
      const blob = await api.remuxMkvToMp4(videoFile);
      setState((prev) => ({ ...prev, isRemuxing: false }));

      // Generate filename
      const filename = videoFile.name.replace(/\.[^/.]+$/, '') + '.mp4';
      api.downloadBlob(blob, filename);

      return blob;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'MKV remux failed';
      setState((prev) => ({
        ...prev,
        isRemuxing: false,
        error: errorMessage,
      }));
      return null;
    }
  }, [state.file]);

  /**
   * Convert video to MP4 with quality option
   */
  const convertToMp4 = useCallback(
    async (
      quality: 'fast' | 'balanced' | 'high' = 'balanced',
      file?: File
    ) => {
      const videoFile = file || state.file;
      if (!videoFile) {
        setState((prev) => ({ ...prev, error: 'No video file selected' }));
        return null;
      }

      setState((prev) => ({ ...prev, isConverting: true, error: null }));

      try {
        const blob = await api.convertToMp4(videoFile, quality);
        setState((prev) => ({ ...prev, isConverting: false }));

        // Generate filename
        const filename = videoFile.name.replace(/\.[^/.]+$/, '') + '.mp4';
        api.downloadBlob(blob, filename);

        return blob;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Video conversion failed';
        setState((prev) => ({
          ...prev,
          isConverting: false,
          error: errorMessage,
        }));
        return null;
      }
    },
    [state.file]
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
      file: null,
      analysis: null,
      isAnalyzing: false,
      isConverting: false,
      isRemuxing: false,
      error: null,
    });
  }, []);

  return {
    // State
    ...state,

    // Actions
    setVideoFile,
    analyzeVideo,
    remuxMkvToMp4,
    convertToMp4,
    clearError,
    reset,
  };
}
