/**
 * API Type Definitions
 * TypeScript interfaces for Scriptum v2.1 API
 */

// Health Check
export interface HealthResponse {
  status: string;
  version: string;
  architecture: string;
  service: string;
}

// Video Analysis
export interface VideoInfo {
  format: string;
  size_mb: number;
  resolution: string;
  duration: number;
  duration_formatted: string;
  codec: string;
  fps: number;
  bitrate?: number;
}

export interface VideoAnalysisResponse {
  success: boolean;
  video_info: VideoInfo;
  can_remux_to_mp4: boolean;
  can_convert_to_mp4: boolean;
}

// Movie Recognition
export interface Movie {
  title: string;
  year: string;
  rating?: number;
  poster?: string;
  overview?: string;
  imdb_id?: string;
  tmdb_id?: number;
}

export interface MovieRecognitionResponse {
  success: boolean;
  movie?: Movie;
  message?: string;
}

// Subtitles
export interface SubtitleEntry {
  index: number;
  timestamp: string;
  text: string;
}

export interface Subtitle {
  file_id: number;
  name: string;
  language: string;
  downloads: number;
  rating: number;
  file_name?: string;
}

export interface SubtitleSearchResponse {
  success: boolean;
  count: number;
  subtitles: Subtitle[];
}

export interface EmbeddedSubtitle {
  index: number;
  language: string;
  title: string;
  codec: string;
  file_name: string;
  content_base64: string;
}

export interface EmbeddedSubtitlesResponse {
  success: boolean;
  count: number;
  subtitles: EmbeddedSubtitle[];
}

// Sync
export interface SyncResponse {
  success: boolean;
  message?: string;
  offset?: number;
  confidence?: number;
}

// Translation
export interface TranslationResponse {
  success: boolean;
  message?: string;
  translated_count?: number;
}

// Error Response
export interface ErrorResponse {
  success: false;
  error: string;
  details?: string;
}

// API Response Types
export type ApiResponse<T> = T | ErrorResponse;
