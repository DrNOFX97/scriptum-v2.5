# React Hooks - Complete

## Summary

All React hooks have been successfully created to replace the ES6 managers from the previous implementation.

## Created Hooks

### 1. `useVideo` (src/hooks/useVideo.ts)
**Purpose**: Manage video file operations

**Features**:
- Set/get video file
- Analyze video (format, codec, resolution, etc.)
- Remux MKV to MP4 (fast, no re-encoding)
- Convert video to MP4 with quality options (fast/balanced/high)
- Loading states: `isAnalyzing`, `isConverting`, `isRemuxing`
- Error handling with `clearError()`
- Reset state

**Usage Example**:
```typescript
import { useVideo } from './hooks';

function VideoComponent() {
  const {
    file,
    analysis,
    isAnalyzing,
    analyzeVideo,
    remuxMkvToMp4
  } = useVideo();

  const handleFileSelect = async (file: File) => {
    await analyzeVideo(file);
  };
}
```

### 2. `useSubtitle` (src/hooks/useSubtitle.ts)
**Purpose**: Manage subtitle operations

**Features**:
- Set/get subtitle file
- Search subtitles on OpenSubtitles (query, language, limit)
- Download subtitle from OpenSubtitles by file ID
- Extract embedded subtitles from MKV files
- Download embedded subtitle (base64 decoding)
- Clear search results
- Loading states: `isSearching`, `isDownloading`, `isExtracting`
- Error handling with `clearError()`
- Reset state

**Usage Example**:
```typescript
import { useSubtitle } from './hooks';

function SubtitleComponent() {
  const {
    searchResults,
    isSearching,
    searchSubtitles,
    downloadSubtitle
  } = useSubtitle();

  const handleSearch = async () => {
    await searchSubtitles('Matrix', 'pt', 10);
  };
}
```

### 3. `useMovieRecognition` (src/hooks/useMovieRecognition.ts)
**Purpose**: Recognize movies via TMDB API

**Features**:
- Recognize movie from filename
- Recognize movie from File object
- Manually set movie data
- Returns movie metadata (title, year, rating, poster, overview, IMDb ID, TMDB ID)
- Loading state: `isRecognizing`
- Error handling with `clearError()`
- Reset state

**Usage Example**:
```typescript
import { useMovieRecognition } from './hooks';

function MovieComponent() {
  const {
    movie,
    isRecognizing,
    recognizeMovieFromFile
  } = useMovieRecognition();

  const handleFileSelect = async (file: File) => {
    const movieData = await recognizeMovieFromFile(file);
    if (movieData) {
      console.log(`Found: ${movieData.title} (${movieData.year})`);
    }
  };
}
```

### 4. `useTranslation` (src/hooks/useTranslation.ts)
**Purpose**: Translate subtitles using Google Gemini

**Features**:
- Translate subtitle file
- Source/target language configuration
- Optional movie context for better translations
- Progress tracking (simulated)
- Auto-download translated file
- Loading state: `isTranslating`
- Progress percentage: `progress` (0-100)
- Error handling with `clearError()`
- Reset state

**Usage Example**:
```typescript
import { useTranslation } from './hooks';

function TranslationComponent() {
  const {
    isTranslating,
    progress,
    translateSubtitle
  } = useTranslation();

  const handleTranslate = async (file: File) => {
    await translateSubtitle(file, {
      sourceLang: 'en',
      targetLang: 'pt',
      movieContext: 'The Matrix (1999)'
    });
  };
}
```

### 5. `useSync` (src/hooks/useSync.ts)
**Purpose**: Synchronize subtitles with video using MLX Whisper

**Features**:
- Sync subtitle with video file
- Progress tracking (simulated)
- Auto-download synced subtitle
- Loading state: `isSyncing`
- Progress percentage: `progress` (0-100)
- Error handling with `clearError()`
- Reset state

**Usage Example**:
```typescript
import { useSync } from './hooks';

function SyncComponent() {
  const {
    isSyncing,
    progress,
    syncSubtitles
  } = useSync();

  const handleSync = async (video: File, subtitle: File) => {
    await syncSubtitles(video, subtitle);
  };
}
```

## Index Export (src/hooks/index.ts)

All hooks are exported from a central index file for convenient importing:

```typescript
// Import individual hooks
import { useVideo, useSubtitle, useSync } from './hooks';

// Import types
import type { VideoState, SubtitleState } from './hooks';
```

## Architecture Benefits

### Type Safety
- Full TypeScript support with exported state types
- IntelliSense for all hook methods and properties
- Compile-time error checking

### Reusability
- Hooks can be used in any React component
- State is isolated per component instance
- Easy to combine multiple hooks

### Clean API
- Consistent naming conventions
- Predictable state management
- Standard loading/error patterns

### Error Handling
- All hooks provide error state
- `clearError()` method for manual error clearing
- Detailed error messages

### State Management
- Each hook manages its own state
- `reset()` method to clear all state
- No global state pollution

## Next Steps

Now that hooks are complete, you can:

1. **Create reusable UI components** that use these hooks
2. **Build pages** for each route in the sitemap
3. **Implement routing** with React Router
4. **Add Zustand stores** for global state (if needed)
5. **Integrate TanStack Query** for data caching

## File Structure

```
frontend/src/hooks/
├── index.ts                    # Central exports
├── useVideo.ts                 # Video operations
├── useSubtitle.ts              # Subtitle operations
├── useMovieRecognition.ts      # TMDB integration
├── useTranslation.ts           # Gemini translation
└── useSync.ts                  # MLX Whisper sync
```

## Testing the Hooks

You can test hooks by importing them in `App.tsx`:

```typescript
import { useVideo, useSubtitle } from './hooks';

function App() {
  const video = useVideo();
  const subtitle = useSubtitle();

  // Use the hooks...
}
```

All hooks are ready to use!
