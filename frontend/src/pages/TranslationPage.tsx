/**
 * TranslationPage
 * Translate subtitles using Google Gemini AI
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks';
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

export default function TranslationPage() {
  const navigate = useNavigate();
  const {
    translatedFile,
    isTranslating,
    progress,
    error,
    translateSubtitle,
    clearError,
    reset,
  } = useTranslation();

  const [subtitleFile, setSubtitleFile] = useState<File | null>(null);
  const [sourceLang, setSourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('pt');
  const [tone, setTone] = useState<'formal' | 'casual' | 'technical'>('casual');
  const [preserveFormatting, setPreserveFormatting] = useState(true);

  const handleFileSelect = (files: File[]) => {
    if (files.length === 0) return;
    setSubtitleFile(files[0]);
    reset();
  };

  const handleTranslate = async () => {
    if (!subtitleFile) return;

    await translateSubtitle(subtitleFile, {
      sourceLang,
      targetLang,
      tone,
      preserveFormatting,
    });
  };

  const handleDownload = () => {
    if (!translatedFile) return;

    const url = URL.createObjectURL(translatedFile);
    const a = document.createElement('a');
    a.href = url;
    a.download = translatedFile.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setSubtitleFile(null);
    reset();
  };

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'pt', name: 'Portuguese (PT)' },
    { code: 'pt-BR', name: 'Portuguese (BR)' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ru', name: 'Russian' },
    { code: 'ar', name: 'Arabic' },
    { code: 'hi', name: 'Hindi' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-400 to-secondary-500">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              🌍 Translate Subtitles
            </h1>
            <p className="text-white/90">
              AI-powered translation with Google Gemini
            </p>
          </div>
          <Button variant="secondary" onClick={() => navigate('/')}>
            ← Back to Dashboard
          </Button>
        </div>

        {/* File Upload */}
        {!subtitleFile && !translatedFile && (
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Upload Subtitle File</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploader
                accept=".srt,.vtt,.ass,.ssa"
                onFileSelect={handleFileSelect}
                label="Select Subtitle File"
                description="Drag and drop your subtitle file or click to browse"
                icon="📝"
                maxSize={10}
              />
            </CardContent>
          </Card>
        )}

        {/* Translation Configuration */}
        {subtitleFile && !translatedFile && (
          <div className="space-y-6">
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Subtitle File</CardTitle>
              </CardHeader>
              <CardContent>
                <FilePreview file={subtitleFile} onRemove={handleReset} />
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Translation Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Language Selection */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Source Language
                      </label>
                      <select
                        value={sourceLang}
                        onChange={(e) => setSourceLang(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        disabled={isTranslating}
                      >
                        {languages.map((lang) => (
                          <option key={lang.code} value={lang.code}>
                            {lang.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Target Language
                      </label>
                      <select
                        value={targetLang}
                        onChange={(e) => setTargetLang(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        disabled={isTranslating}
                      >
                        {languages.map((lang) => (
                          <option key={lang.code} value={lang.code}>
                            {lang.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Tone Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Translation Tone
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {(['formal', 'casual', 'technical'] as const).map((t) => (
                        <button
                          key={t}
                          type="button"
                          onClick={() => setTone(t)}
                          disabled={isTranslating}
                          className={`px-4 py-2 rounded-lg border-2 font-medium transition-colors ${
                            tone === t
                              ? 'border-primary-500 bg-primary-50 text-primary-700'
                              : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                          } ${isTranslating ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          {t.charAt(0).toUpperCase() + t.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Options */}
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="preserveFormatting"
                      checked={preserveFormatting}
                      onChange={(e) => setPreserveFormatting(e.target.checked)}
                      disabled={isTranslating}
                      className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    />
                    <label
                      htmlFor="preserveFormatting"
                      className="ml-2 text-sm text-gray-700"
                    >
                      Preserve timing and formatting
                    </label>
                  </div>

                  <Button
                    onClick={handleTranslate}
                    isLoading={isTranslating}
                    disabled={sourceLang === targetLang}
                    fullWidth
                  >
                    {isTranslating ? 'Translating...' : 'Translate Subtitle'}
                  </Button>

                  {sourceLang === targetLang && (
                    <Alert variant="warning" title="Warning">
                      Source and target languages cannot be the same
                    </Alert>
                  )}

                  {error && (
                    <Alert variant="error" title="Error" onClose={clearError}>
                      {error}
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Progress */}
            {isTranslating && (
              <Card variant="elevated">
                <CardHeader>
                  <CardTitle>Translation Progress</CardTitle>
                </CardHeader>
                <CardContent>
                  <ProgressBar
                    progress={progress}
                    label={`Translating... ${progress}%`}
                  />
                  <p className="text-sm text-gray-600 mt-3 text-center">
                    Please wait while Google Gemini translates your subtitle file
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Translation Complete */}
        {translatedFile && (
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Translation Complete</CardTitle>
            </CardHeader>
            <CardContent>
              <Alert variant="success" title="Success" className="mb-4">
                Your subtitle has been translated successfully!
              </Alert>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600 mb-1">Original File</p>
                    <p className="font-medium">{subtitleFile?.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 mb-1">Translated File</p>
                    <p className="font-medium">{translatedFile.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 mb-1">Languages</p>
                    <p className="font-medium">
                      {languages.find((l) => l.code === sourceLang)?.name} →{' '}
                      {languages.find((l) => l.code === targetLang)?.name}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600 mb-1">Tone</p>
                    <p className="font-medium capitalize">{tone}</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button onClick={handleDownload} fullWidth>
                  📥 Download Translated File
                </Button>
                <Button onClick={handleReset} variant="secondary" fullWidth>
                  🔄 Translate Another
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info Box */}
        <Card variant="default" className="mt-6">
          <CardContent className="bg-blue-50">
            <h3 className="font-semibold text-blue-900 mb-3">
              ℹ️ Translation Features
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
              <div>
                <h4 className="font-semibold mb-2">🤖 AI-Powered</h4>
                <ul className="space-y-1">
                  <li>• Google Gemini language model</li>
                  <li>• Context-aware translations</li>
                  <li>• Natural language output</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">⚙️ Customization</h4>
                <ul className="space-y-1">
                  <li>• Multiple tone options</li>
                  <li>• Preserves timing codes</li>
                  <li>• Maintains formatting</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
