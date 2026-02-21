/**
 * Dashboard Page
 * Main landing page for the application
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVideo, useMovieRecognition } from '../hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  FileUploader,
  FilePreview,
  Button,
  Alert,
  VideoInfo,
  MovieCard,
} from '../components';

export default function Dashboard() {
  const navigate = useNavigate();
  const {
    file: videoFile,
    analysis,
    isAnalyzing,
    error: videoError,
    setVideoFile,
    analyzeVideo,
    clearError: clearVideoError,
  } = useVideo();

  const {
    movie,
    isRecognizing,
    recognizeMovieFromFile,
  } = useMovieRecognition();

  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleVideoSelect = async (files: File[]) => {
    if (files.length === 0) return;

    const file = files[0];
    setVideoFile(file);
    setShowAnalysis(false);

    // Recognize movie from filename
    await recognizeMovieFromFile(file);
  };

  const handleAnalyze = async () => {
    if (!videoFile) return;
    const result = await analyzeVideo();
    if (result) {
      setShowAnalysis(true);
    }
  };

  const handleRemoveVideo = () => {
    setVideoFile(null);
    setShowAnalysis(false);
    clearVideoError();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-gray-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block mb-6 px-8 py-3 bg-gradient-to-r from-primary-500/30 to-secondary-500/30 rounded-full border border-primary-300/60 shadow-glow">
            <span className="text-cyan-200 font-bold text-sm tracking-widest uppercase">Version 2.1</span>
          </div>
          <h1 className="text-7xl font-black bg-gradient-to-r from-cyan-200 via-blue-200 to-purple-200 bg-clip-text text-transparent mb-4 tracking-tight animate-text-glow">
            Scriptum
          </h1>
          <p className="text-gray-100 text-2xl font-semibold tracking-wide mb-6 drop-shadow-lg">
            Professional Subtitle Translation & Synchronization
          </p>
          <div className="mt-6 flex items-center justify-center gap-4 text-base font-medium">
            <span className="flex items-center gap-2 bg-emerald-500/20 px-4 py-2 rounded-lg border border-emerald-400/50">
              <span className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-pulse shadow-glow"></span>
              <span className="text-emerald-200">AI-Powered</span>
            </span>
            <span className="text-gray-400">•</span>
            <span className="text-gray-200">MLX Whisper</span>
            <span className="text-gray-400">•</span>
            <span className="text-gray-200">Google Gemini</span>
          </div>
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* File Upload Section */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Upload Video File</CardTitle>
            </CardHeader>
            <CardContent>
              {!videoFile ? (
                <FileUploader
                  accept="video/*,.mkv,.avi,.mov,.wmv,.flv,.webm"
                  onFileSelect={handleVideoSelect}
                  label="Select Video File"
                  description="Drag and drop your video file or click to browse (MP4, MKV, AVI, MOV, etc.)"
                  icon="🎥"
                  maxSize={2000}
                />
              ) : (
                <div className="space-y-4">
                  <FilePreview file={videoFile} onRemove={handleRemoveVideo} />

                  {!showAnalysis && (
                    <Button
                      onClick={handleAnalyze}
                      isLoading={isAnalyzing}
                      fullWidth
                    >
                      Analyze Video
                    </Button>
                  )}
                </div>
              )}

              {videoError && (
                <Alert
                  variant="error"
                  title="Error"
                  onClose={clearVideoError}
                  className="mt-4"
                >
                  {videoError}
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Movie Recognition */}
          {(movie || isRecognizing) && (
            <div className="animate-slide-up">
              {isRecognizing ? (
                <Card variant="elevated">
                  <CardContent className="text-center py-16 bg-gradient-to-br from-slate-800/95 to-slate-900/95">
                    <div className="inline-block animate-spin w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full mb-6 shadow-glow" />
                    <p className="text-gray-100 text-xl font-semibold">Recognizing movie from TMDB...</p>
                    <p className="text-gray-400 text-sm mt-2">Searching database for movie information</p>
                  </CardContent>
                </Card>
              ) : movie ? (
                <MovieCard movie={movie} />
              ) : null}
            </div>
          )}

          {/* Video Analysis */}
          {showAnalysis && analysis && (
            <div className="animate-fadeIn">
              <VideoInfo analysis={analysis} />
            </div>
          )}

          {/* Quick Actions */}
          {videoFile && showAnalysis && (
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button
                    variant="secondary"
                    fullWidth
                    onClick={() => navigate('/subtitles/search')}
                  >
                    📝 Search Subtitles
                  </Button>
                  <Button
                    variant="secondary"
                    fullWidth
                    onClick={() => navigate('/translate')}
                  >
                    🌍 Translate
                  </Button>
                  <Button
                    variant="secondary"
                    fullWidth
                    onClick={() => navigate('/sync')}
                  >
                    🔄 Synchronize
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Info Box */}
          <Card variant="default">
            <CardContent className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 border border-cyan-500/30">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/40 to-blue-500/40 flex items-center justify-center border border-cyan-400/60 shadow-glow">
                  <span className="text-3xl">💡</span>
                </div>
                <div>
                  <h3 className="font-bold text-white text-xl mb-1 drop-shadow-lg">
                    Workflow Overview
                  </h3>
                  <p className="text-gray-200 text-base font-semibold">Professional subtitle processing pipeline</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 bg-cyan-500/20 px-4 py-2 rounded-lg border border-cyan-400/50">
                    <span className="text-2xl">🎥</span>
                    <span className="text-cyan-200 font-bold text-base">Video Processing</span>
                  </div>
                  <ul className="space-y-3 text-base text-gray-200 font-medium">
                    <li className="flex items-start gap-3 hover:text-white transition-colors">
                      <span className="text-cyan-300 mt-1 font-bold text-lg">→</span>
                      <span>Analyze video format and properties</span>
                    </li>
                    <li className="flex items-start gap-3 hover:text-white transition-colors">
                      <span className="text-cyan-300 mt-1 font-bold text-lg">→</span>
                      <span>Convert MKV to MP4 (remux or re-encode)</span>
                    </li>
                    <li className="flex items-start gap-3 hover:text-white transition-colors">
                      <span className="text-cyan-300 mt-1 font-bold text-lg">→</span>
                      <span>Extract embedded subtitles</span>
                    </li>
                  </ul>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 bg-purple-500/20 px-4 py-2 rounded-lg border border-purple-400/50">
                    <span className="text-2xl">📝</span>
                    <span className="text-purple-200 font-bold text-base">Subtitle Management</span>
                  </div>
                  <ul className="space-y-3 text-base text-gray-200 font-medium">
                    <li className="flex items-start gap-3 hover:text-white transition-colors">
                      <span className="text-purple-300 mt-1 font-bold text-lg">→</span>
                      <span>Search OpenSubtitles database</span>
                    </li>
                    <li className="flex items-start gap-3 hover:text-white transition-colors">
                      <span className="text-purple-300 mt-1 font-bold text-lg">→</span>
                      <span>Translate with Google Gemini AI</span>
                    </li>
                    <li className="flex items-start gap-3 hover:text-white transition-colors">
                      <span className="text-purple-300 mt-1 font-bold text-lg">→</span>
                      <span>Sync with MLX Whisper</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
