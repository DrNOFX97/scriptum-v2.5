/**
 * VideoInfo Component
 * Display video analysis information
 */

import type { VideoAnalysisResponse } from '../types/api';
import { Card, CardHeader, CardTitle, CardContent } from './Card';

export interface VideoInfoProps {
  analysis: VideoAnalysisResponse;
}

export function VideoInfo({ analysis }: VideoInfoProps) {
  const { video_info, can_remux_to_mp4, can_convert_to_mp4 } = analysis;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span>🎬</span>
          <span>Video Information</span>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {/* Format */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500 uppercase mb-1">Format</p>
            <p className="text-lg font-semibold text-gray-800">
              {video_info.format.toUpperCase()}
            </p>
          </div>

          {/* Size */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500 uppercase mb-1">File Size</p>
            <p className="text-lg font-semibold text-gray-800">
              {video_info.size_mb.toFixed(1)} MB
            </p>
          </div>

          {/* Resolution */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500 uppercase mb-1">Resolution</p>
            <p className="text-lg font-semibold text-gray-800">
              {video_info.resolution}
            </p>
          </div>

          {/* Duration */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500 uppercase mb-1">Duration</p>
            <p className="text-lg font-semibold text-gray-800">
              {video_info.duration_formatted}
            </p>
          </div>

          {/* Codec */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500 uppercase mb-1">Codec</p>
            <p className="text-lg font-semibold text-gray-800">
              {video_info.codec}
            </p>
          </div>

          {/* FPS */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500 uppercase mb-1">Frame Rate</p>
            <p className="text-lg font-semibold text-gray-800">
              {video_info.fps} fps
            </p>
          </div>

          {/* Bitrate (if available) */}
          {video_info.bitrate && (
            <div className="bg-gray-50 p-3 rounded-lg col-span-2">
              <p className="text-xs text-gray-500 uppercase mb-1">Bitrate</p>
              <p className="text-lg font-semibold text-gray-800">
                {(video_info.bitrate / 1000).toFixed(0)} kbps
              </p>
            </div>
          )}
        </div>

        {/* Conversion Options */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm font-semibold text-blue-900 mb-2">
            Conversion Options
          </p>
          <div className="space-y-1 text-sm text-blue-800">
            {can_remux_to_mp4 && (
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Can remux to MP4 (fast, no re-encoding)</span>
              </div>
            )}
            {can_convert_to_mp4 && (
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Can convert to MP4 (slower, re-encoding)</span>
              </div>
            )}
            {!can_remux_to_mp4 && !can_convert_to_mp4 && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500">—</span>
                <span>No conversion needed (already MP4)</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
