/**
 * API Client - TypeScript
 * REST API client for Scriptum v2.1 backend
 * Refactored with improved error handling and utilities
 */

import type {
  HealthResponse,
  VideoAnalysisResponse,
  MovieRecognitionResponse,
  SubtitleSearchResponse,
  EmbeddedSubtitlesResponse,
  SyncResponse,
  TranslationResponse,
  ErrorResponse,
} from '../types/api';
import { API_BASE_URL, API_TIMEOUT } from '../lib/constants';
import { ApiError, NetworkError } from '../lib/errors';

class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = API_BASE_URL, timeout: number = API_TIMEOUT) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Internal fetch wrapper with timeout and error handling
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new NetworkError('Request timeout', url);
      }
      throw NetworkError.fromError(error, url);
    }
  }

  /**
   * Handle API response errors
   */
  private async handleResponse<T>(
    response: Response,
    endpoint: string
  ): Promise<T> {
    if (!response.ok) {
      let errorMessage: string;
      try {
        const error: ErrorResponse = await response.json();
        errorMessage = error.error || 'Request failed';
      } catch {
        errorMessage = response.statusText || 'Request failed';
      }
      throw new ApiError(errorMessage, response.status, endpoint);
    }
    return response.json();
  }

  /**
   * Handle blob response errors
   */
  private async handleBlobResponse(
    response: Response,
    endpoint: string
  ): Promise<Blob> {
    if (!response.ok) {
      let errorMessage: string;
      try {
        const error: ErrorResponse = await response.json();
        errorMessage = error.error || 'Request failed';
      } catch {
        errorMessage = response.statusText || 'Request failed';
      }
      throw new ApiError(errorMessage, response.status, endpoint);
    }
    return response.blob();
  }

  /**
   * Health check
   */
  async health(): Promise<HealthResponse> {
    const endpoint = '/health';
    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`);
    return this.handleResponse<HealthResponse>(response, endpoint);
  }

  /**
   * Analyze video file
   */
  async analyzeVideo(videoFile: File): Promise<VideoAnalysisResponse> {
    const endpoint = '/analyze-video';
    const formData = new FormData();
    formData.append('video', videoFile);

    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<VideoAnalysisResponse>(response, endpoint);
  }

  /**
   * Recognize movie from filename
   */
  async recognizeMovie(
    filename: string,
    imdbId?: string
  ): Promise<MovieRecognitionResponse> {
    const endpoint = '/recognize-movie';
    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, imdb_id: imdbId }),
    });

    return this.handleResponse<MovieRecognitionResponse>(response, endpoint);
  }

  /**
   * Remux MKV to MP4 (fast, no re-encoding)
   */
  async remuxMkvToMp4(videoFile: File): Promise<Blob> {
    const endpoint = '/remux-mkv-to-mp4';
    const formData = new FormData();
    formData.append('video', videoFile);

    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return this.handleBlobResponse(response, endpoint);
  }

  /**
   * Convert video to MP4 with quality option
   */
  async convertToMp4(
    videoFile: File,
    quality: 'fast' | 'balanced' | 'high' = 'balanced'
  ): Promise<Blob> {
    const endpoint = '/convert-to-mp4';
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('quality', quality);

    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return this.handleBlobResponse(response, endpoint);
  }

  /**
   * Extract embedded subtitles from MKV
   */
  async extractMkvSubtitles(
    videoFile: File
  ): Promise<EmbeddedSubtitlesResponse> {
    const endpoint = '/extract-mkv-subtitles';
    const formData = new FormData();
    formData.append('video', videoFile);

    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<EmbeddedSubtitlesResponse>(response, endpoint);
  }

  /**
   * Search subtitles on OpenSubtitles
   */
  async searchSubtitles(
    query: string,
    language: string = 'pt',
    limit: number = 10
  ): Promise<SubtitleSearchResponse> {
    const endpoint = '/search-subtitles';
    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, language, limit }),
    });

    return this.handleResponse<SubtitleSearchResponse>(response, endpoint);
  }

  /**
   * Download subtitle from OpenSubtitles
   */
  async downloadSubtitle(fileId: number): Promise<Blob> {
    const endpoint = '/download-subtitle';
    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId }),
    });

    return this.handleBlobResponse(response, endpoint);
  }

  /**
   * Synchronize subtitle with video using MLX Whisper
   */
  async syncSubtitles(
    videoFile: File,
    subtitleFile: File
  ): Promise<Blob> {
    const endpoint = '/sync';
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('subtitle', subtitleFile);

    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return this.handleBlobResponse(response, endpoint);
  }

  /**
   * Translate subtitle using Google Gemini
   */
  async translateSubtitle(
    subtitleFile: File,
    sourceLang: string,
    targetLang: string,
    movieContext?: string
  ): Promise<Blob> {
    const endpoint = '/translate';
    const formData = new FormData();
    formData.append('subtitle', subtitleFile);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);
    if (movieContext) {
      formData.append('movie_context', movieContext);
    }

    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return this.handleBlobResponse(response, endpoint);
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing
export { ApiClient };
