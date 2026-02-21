/**
 * FileUploader Component
 * Drag-and-drop file upload with preview
 */

import { useCallback, useState, DragEvent, ChangeEvent } from 'react';

export interface FileUploaderProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in MB
  onFileSelect: (files: File[]) => void;
  label?: string;
  description?: string;
  icon?: string;
}

export function FileUploader({
  accept = '*/*',
  multiple = false,
  maxSize = 500, // 500MB default
  onFileSelect,
  label = 'Upload File',
  description = 'Drag and drop or click to browse',
  icon = '📁',
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFiles = useCallback(
    (files: FileList | null): File[] => {
      if (!files || files.length === 0) return [];

      const validFiles: File[] = [];
      const maxSizeBytes = maxSize * 1024 * 1024;

      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Check file size
        if (file.size > maxSizeBytes) {
          setError(`File ${file.name} exceeds maximum size of ${maxSize}MB`);
          continue;
        }

        validFiles.push(file);
      }

      return validFiles;
    },
    [maxSize]
  );

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      setError(null);

      const files = validateFiles(e.dataTransfer.files);
      if (files.length > 0) {
        onFileSelect(files);
      }
    },
    [validateFiles, onFileSelect]
  );

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      setError(null);
      const files = validateFiles(e.target.files);
      if (files.length > 0) {
        onFileSelect(files);
      }
      // Reset input value to allow selecting the same file again
      e.target.value = '';
    },
    [validateFiles, onFileSelect]
  );

  return (
    <div className="w-full">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8
          transition-all duration-200 cursor-pointer
          ${
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
        `}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center gap-3">
          <div className="text-6xl">{icon}</div>
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">{label}</p>
            <p className="text-sm text-gray-500 mt-1">{description}</p>
            <p className="text-xs text-gray-400 mt-2">
              Maximum file size: {maxSize}MB
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}

export interface FilePreviewProps {
  file: File;
  onRemove?: () => void;
}

export function FilePreview({ file, onRemove }: FilePreviewProps) {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const iconMap: Record<string, string> = {
      mp4: '🎥',
      mkv: '🎬',
      avi: '🎞️',
      mov: '📹',
      srt: '📝',
      vtt: '📄',
      sub: '📋',
      txt: '📃',
    };
    return iconMap[ext || ''] || '📁';
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="text-3xl">{getFileIcon(file.name)}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
      </div>
      {onRemove && (
        <button
          onClick={onRemove}
          className="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors"
          aria-label="Remove file"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
