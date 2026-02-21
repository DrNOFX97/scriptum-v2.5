/**
 * useSync Hook
 * React hook for subtitle synchronization using MLX Whisper
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';

export interface SyncState {
  isSyncing: boolean;
  progress: number;
  error: string | null;
}

export function useSync() {
  const [state, setState] = useState<SyncState>({
    isSyncing: false,
    progress: 0,
    error: null,
  });

  /**
   * Synchronize subtitle with video
   */
  const syncSubtitles = useCallback(
    async (videoFile: File, subtitleFile: File): Promise<Blob | null> => {
      setState({ isSyncing: true, progress: 0, error: null });

      try {
        // Simulate progress (since API doesn't provide real-time progress)
        const progressInterval = setInterval(() => {
          setState((prev) => ({
            ...prev,
            progress: Math.min(prev.progress + 5, 90),
          }));
        }, 1000);

        const blob = await api.syncSubtitles(videoFile, subtitleFile);

        clearInterval(progressInterval);

        setState({
          isSyncing: false,
          progress: 100,
          error: null,
        });

        // Generate filename
        const originalName = subtitleFile.name.replace(/\.[^/.]+$/, '');
        const filename = `${originalName}_synced.srt`;
        api.downloadBlob(blob, filename);

        return blob;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Synchronization failed';
        setState({
          isSyncing: false,
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
      isSyncing: false,
      progress: 0,
      error: null,
    });
  }, []);

  return {
    // State
    ...state,

    // Actions
    syncSubtitles,
    clearError,
    reset,
  };
}
