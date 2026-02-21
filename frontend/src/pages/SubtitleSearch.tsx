/**
 * SubtitleSearch Page
 * Search and download subtitles from OpenSubtitles
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubtitle } from '../hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Alert,
  SubtitleSearchResults,
} from '../components';

export default function SubtitleSearch() {
  const navigate = useNavigate();
  const {
    searchResults,
    isSearching,
    isDownloading,
    error,
    searchSubtitles,
    downloadSubtitle,
    clearError,
  } = useSubtitle();

  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('pt');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    await searchSubtitles(query, language, 20);
  };

  const handleDownload = async (fileId: number, filename: string) => {
    await downloadSubtitle(fileId, filename);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-400 to-secondary-500">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              📝 Search Subtitles
            </h1>
            <p className="text-white/90">
              Find subtitles from OpenSubtitles database
            </p>
          </div>
          <Button variant="secondary" onClick={() => navigate('/')}>
            ← Back to Dashboard
          </Button>
        </div>

        {/* Search Form */}
        <Card variant="elevated" className="mb-6">
          <CardHeader>
            <CardTitle>Search OpenSubtitles</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Search Query */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Movie or TV Show Name
                  </label>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., The Matrix, Breaking Bad S01E01"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  />
                </div>

                {/* Language */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="pt">Portuguese (PT)</option>
                    <option value="pt-BR">Portuguese (BR)</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                    <option value="zh">Chinese</option>
                    <option value="ru">Russian</option>
                  </select>
                </div>
              </div>

              <Button
                type="submit"
                isLoading={isSearching}
                disabled={!query.trim()}
                fullWidth
              >
                {isSearching ? 'Searching...' : 'Search Subtitles'}
              </Button>
            </form>

            {error && (
              <Alert variant="error" title="Error" onClose={clearError} className="mt-4">
                {error}
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>
                Search Results ({searchResults.length} found)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SubtitleSearchResults
                subtitles={searchResults}
                onDownload={handleDownload}
                isDownloading={isDownloading}
              />
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {!isSearching && searchResults.length === 0 && !error && (
          <Card variant="elevated">
            <CardContent className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-gray-600 text-lg mb-2">
                Search for subtitles
              </p>
              <p className="text-gray-500 text-sm">
                Enter a movie or TV show name above to get started
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
