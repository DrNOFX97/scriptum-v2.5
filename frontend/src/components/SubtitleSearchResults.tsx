/**
 * SubtitleSearchResults Component
 * Display subtitle search results from OpenSubtitles
 */

import type { Subtitle } from '../types/api';
import { Button } from './Button';

export interface SubtitleSearchResultsProps {
  subtitles: Subtitle[];
  onDownload: (fileId: number, filename: string) => void;
  isDownloading?: boolean;
}

export function SubtitleSearchResults({
  subtitles,
  onDownload,
  isDownloading = false,
}: SubtitleSearchResultsProps) {
  if (subtitles.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <p className="text-gray-600">No subtitles found</p>
        <p className="text-sm text-gray-500 mt-2">
          Try a different search query
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {subtitles.map((subtitle) => (
        <SubtitleItem
          key={subtitle.file_id}
          subtitle={subtitle}
          onDownload={onDownload}
          isDownloading={isDownloading}
        />
      ))}
    </div>
  );
}

interface SubtitleItemProps {
  subtitle: Subtitle;
  onDownload: (fileId: number, filename: string) => void;
  isDownloading: boolean;
}

function SubtitleItem({ subtitle, onDownload, isDownloading }: SubtitleItemProps) {
  const getLanguageFlag = (lang: string): string => {
    const flagMap: Record<string, string> = {
      pt: '🇵🇹',
      'pt-BR': '🇧🇷',
      en: '🇬🇧',
      es: '🇪🇸',
      fr: '🇫🇷',
      de: '🇩🇪',
      it: '🇮🇹',
      ja: '🇯🇵',
      ko: '🇰🇷',
      zh: '🇨🇳',
      ru: '🇷🇺',
    };
    return flagMap[lang] || '🌐';
  };

  const getRatingColor = (rating: number): string => {
    if (rating >= 8) return 'text-green-600';
    if (rating >= 6) return 'text-yellow-600';
    return 'text-gray-500';
  };

  return (
    <div className="flex items-start gap-4 p-4 bg-white border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-md transition-all">
      {/* Language Flag */}
      <div className="text-3xl">{getLanguageFlag(subtitle.language)}</div>

      {/* Subtitle Info */}
      <div className="flex-1 min-w-0">
        <h4 className="text-base font-semibold text-gray-800 truncate">
          {subtitle.name}
        </h4>
        {subtitle.file_name && (
          <p className="text-sm text-gray-500 truncate mt-1">{subtitle.file_name}</p>
        )}

        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
          {/* Language */}
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733 18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.894L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z"
                clipRule="evenodd"
              />
            </svg>
            <span>{subtitle.language.toUpperCase()}</span>
          </span>

          {/* Downloads */}
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
            <span>{subtitle.downloads.toLocaleString()}</span>
          </span>

          {/* Rating */}
          {subtitle.rating > 0 && (
            <span className={`flex items-center gap-1 ${getRatingColor(subtitle.rating)}`}>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span>{subtitle.rating.toFixed(1)}</span>
            </span>
          )}
        </div>
      </div>

      {/* Download Button */}
      <Button
        size="sm"
        onClick={() => onDownload(subtitle.file_id, subtitle.file_name || subtitle.name)}
        disabled={isDownloading}
        isLoading={isDownloading}
      >
        Download
      </Button>
    </div>
  );
}
