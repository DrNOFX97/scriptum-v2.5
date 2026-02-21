/**
 * SyncPage
 * Synchronize subtitles with MLX Whisper
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSync } from '../hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  FileUploader,
  FilePreview,
  Button,
  Alert,
  ProgressBar,
} from '../components';

export default function SyncPage() {
  const navigate = useNavigate();
  const {
    syncedFile,
    isSyncing,
    progress,
    error,
    syncSubtitle,
    clearError,
    reset,
  } = useSync();

  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [subtitleFile, setSubtitleFile] = useState<File | null>(null);
  const [model, setModel] = useState<'tiny' | 'base' | 'small' | 'medium'>('base');
  const [language, setLanguage] = useState('auto');

  const handleVideoSelect = (files: File[]) => {
    if (files.length === 0) return;
    setVideoFile(files[0]);
  };

  const handleSubtitleSelect = (files: File[]) => {
    if (files.length === 0) return;
    setSubtitleFile(files[0]);
  };

  const handleSync = async () => {
    if (!videoFile || !subtitleFile) return;

    await syncSubtitle(videoFile, subtitleFile, {
      model,
      language: language === 'auto' ? undefined : language,
    });
  };

  const handleDownload = () => {
    if (!syncedFile) return;

    const url = URL.createObjectURL(syncedFile);
    const a = document.createElement('a');
    a.href = url;
    a.download = syncedFile.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setVideoFile(null);
    setSubtitleFile(null);
    reset();
  };

  const languages = [
    { code: 'auto', name: 'Auto-detect' },
    { code: 'en', name: 'English' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ru', name: 'Russian' },
  ];

  const models = [
    { value: 'tiny', name: 'Tiny', description: 'Fastest, least accurate' },
    { value: 'base', name: 'Base', description: 'Good balance (recommended)' },
    { value: 'small', name: 'Small', description: 'More accurate, slower' },
    { value: 'medium', name: 'Medium', description: 'Most accurate, slowest' },
  ] as const;

  const canSync = videoFile && subtitleFile && !isSyncing;

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-400 to-secondary-500">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              🔄 Synchronize Subtitles
            </h1>
            <p className="text-white/90">
              Sync subtitles with video using MLX Whisper
            </p>
          </div>
          <Button variant="secondary" onClick={() => navigate('/')}>
            ← Back to Dashboard
          </Button>
        </div>

        {/* File Upload */}
        {!syncedFile && (
          <div className="space-y-6">
            {/* Video File */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>1. Upload Video File</CardTitle>
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
                  <FilePreview
                    file={videoFile}
                    onRemove={() => setVideoFile(null)}
                  />
                )}
              </CardContent>
            </Card>

            {/* Subtitle File */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>2. Upload Subtitle File</CardTitle>
              </CardHeader>
              <CardContent>
                {!subtitleFile ? (
                  <FileUploader
                    accept=".srt,.vtt,.ass,.ssa"
                    onFileSelect={handleSubtitleSelect}
                    label="Select Subtitle File"
                    description="Drag and drop your subtitle file or click to browse"
                    icon="📝"
                    maxSize={10}
                  />
                ) : (
                  <FilePreview
                    file={subtitleFile}
                    onRemove={() => setSubtitleFile(null)}
                  />
                )}
              </CardContent>
            </Card>

            {/* Sync Settings */}
            {videoFile && subtitleFile && (
              <Card variant="elevated">
                <CardHeader>
                  <CardTitle>3. Synchronization Settings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Model Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Whisper Model
                      </label>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        {models.map((m) => (
                          <button
                            key={m.value}
                            type="button"
                            onClick={() => setModel(m.value)}
                            disabled={isSyncing}
                            className={`px-4 py-3 rounded-lg border-2 transition-colors ${
                              model === m.value
                                ? 'border-primary-500 bg-primary-50'
                                : 'border-gray-300 bg-white hover:border-gray-400'
                            } ${isSyncing ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            <div className="font-medium text-gray-900">
                              {m.name}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              {m.description}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Language Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Audio Language
                      </label>
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        disabled={isSyncing}
                      >
                        {languages.map((lang) => (
                          <option key={lang.code} value={lang.code}>
                            {lang.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <Button
                      onClick={handleSync}
                      isLoading={isSyncing}
                      disabled={!canSync}
                      fullWidth
                    >
                      {isSyncing ? 'Synchronizing...' : 'Start Synchronization'}
                    </Button>

                    {error && (
                      <Alert variant="error" title="Error" onClose={clearError}>
                        {error}
                      </Alert>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Progress */}
            {isSyncing && (
              <Card variant="elevated">
                <CardHeader>
                  <CardTitle>Synchronization Progress</CardTitle>
                </CardHeader>
                <CardContent>
                  <ProgressBar
                    progress={progress}
                    label={`Processing... ${progress}%`}
                  />
                  <div className="mt-4 space-y-2 text-sm text-gray-600">
                    <div className="flex items-center justify-between">
                      <span>🎤 Extracting audio from video</span>
                      <span className={progress > 20 ? 'text-green-600' : ''}>
                        {progress > 20 ? '✓' : '...'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>🤖 Running MLX Whisper transcription</span>
                      <span className={progress > 60 ? 'text-green-600' : ''}>
                        {progress > 60 ? '✓' : '...'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>🔄 Aligning subtitle timestamps</span>
                      <span className={progress > 90 ? 'text-green-600' : ''}>
                        {progress > 90 ? '✓' : '...'}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Sync Complete */}
        {syncedFile && (
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Synchronization Complete</CardTitle>
            </CardHeader>
            <CardContent>
              <Alert variant="success" title="Success" className="mb-4">
                Your subtitle has been synchronized successfully!
              </Alert>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600 mb-1">Video File</p>
                    <p className="font-medium">{videoFile?.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 mb-1">Original Subtitle</p>
                    <p className="font-medium">{subtitleFile?.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 mb-1">Synced Subtitle</p>
                    <p className="font-medium">{syncedFile.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 mb-1">Model Used</p>
                    <p className="font-medium capitalize">{model}</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button onClick={handleDownload} fullWidth>
                  📥 Download Synced File
                </Button>
                <Button onClick={handleReset} variant="secondary" fullWidth>
                  🔄 Sync Another
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info Box */}
        <Card variant="default" className="mt-6">
          <CardContent className="bg-blue-50">
            <h3 className="font-semibold text-blue-900 mb-3">
              ℹ️ Synchronization Features
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
              <div>
                <h4 className="font-semibold mb-2">🎯 MLX Whisper</h4>
                <ul className="space-y-1">
                  <li>• State-of-the-art speech recognition</li>
                  <li>• Accurate timestamp alignment</li>
                  <li>• Multiple model sizes for speed/accuracy</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">⚡ Processing</h4>
                <ul className="space-y-1">
                  <li>• Automatic audio extraction</li>
                  <li>• Smart timestamp correction</li>
                  <li>• Preserves subtitle formatting</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
