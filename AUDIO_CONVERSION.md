# Audio Conversion System

## Overview

Server-side audio conversion system for handling large video files with browser-incompatible audio codecs (AC3, DTS, etc.).

### Problem Solved

**Issue**: ffmpeg.wasm in browser fails with files >2GB due to memory limitations.

**Solution**: Move audio conversion to backend with:
- No memory limits (server-side ffmpeg)
- Job-based architecture with progress tracking
- Firestore persistence for cross-instance job tracking
- Similar to translation system pattern

## Architecture

```
Frontend (Browser)               Backend (Cloud Run)
─────────────────               ────────────────────
┌─────────────────┐            ┌──────────────────┐
│ Quick Detection │            │                  │
│  (ffmpeg.wasm)  │            │  Audio Convert   │
│   < 100MB file  │            │     Service      │
└────────┬────────┘            └────────┬─────────┘
         │                              │
         │ File > 2GB                   │
         ├──────────Upload──────────────►
         │                              │
         │                         ┌────▼────┐
         │                         │ Create  │
         │                         │  Job    │
         │                         └────┬────┘
         │                              │
         │                         ┌────▼────┐
         │                         │Firestore│
         │◄────Poll Status─────────┤  Jobs   │
         │                         └────┬────┘
         │                              │
         │                         ┌────▼────┐
         │                         │ ffmpeg  │
         │                         │AC3 → AAC│
         │                         └────┬────┘
         │                              │
         │◄────Download─────────────────┘
         │
```

## Backend Implementation

### 1. Audio Conversion Service
**File**: `/src/scriptum_api/services/audio_conversion_service.py`

Features:
- Detect audio codec (ffprobe)
- Convert AC3/DTS/EAC3 → AAC
- Progress tracking via callbacks
- File size estimation
- Time estimation

Methods:
```python
detect_audio_codec(video_path) → AudioInfo
convert_audio_to_aac(input, output, callback) → bool
estimate_conversion_time(file_size_gb) → str
```

### 2. Audio Conversion Routes
**File**: `/src/scriptum_api/routes/audio_conversion.py`

Endpoints:

#### POST /detect-audio-codec
Quick codec detection (no conversion)
```bash
curl -X POST -F "video=@file.mkv" \
  https://api.example.com/detect-audio-codec
```

Response:
```json
{
  "success": true,
  "has_audio": true,
  "audio_info": {
    "codec": "ac3",
    "channels": 6,
    "channel_layout": "5.1",
    "sample_rate": "48000",
    "is_compatible": false
  },
  "file_size_gb": 5.6,
  "estimated_conversion_time": "5-11 minutes",
  "needs_conversion": true
}
```

#### POST /convert-audio-mkv
Start conversion job
```bash
curl -X POST -F "video=@file.mkv" \
  https://api.example.com/convert-audio-mkv
```

Response:
```json
{
  "success": true,
  "job_id": "a1b2c3d4-...",
  "file_size_gb": 5.6,
  "estimated_time": "5-11 minutes"
}
```

#### GET /convert-audio-status/{job_id}
Poll conversion status
```bash
curl https://api.example.com/convert-audio-status/a1b2c3d4
```

Response:
```json
{
  "success": true,
  "status": "processing",
  "progress": {
    "status": "processing",
    "percentage": 45,
    "message": "Converting audio: 45%"
  },
  "filename": "movie.mkv",
  "output_filename": "movie.web.mkv"
}
```

#### GET /convert-audio-download/{job_id}
Download converted file
```bash
curl -O https://api.example.com/convert-audio-download/a1b2c3d4
```

Returns: Video file with AAC audio

#### POST /convert-audio-cancel/{job_id}
Cancel conversion job
```bash
curl -X POST https://api.example.com/convert-audio-cancel/a1b2c3d4
```

### 3. Job Storage (Firestore)
**Collection**: `translation_jobs` (reused from translation system)

Job document structure:
```json
{
  "status": "processing",
  "filename": "movie.mkv",
  "output_filename": "movie.web.mkv",
  "file_size_gb": 5.6,
  "estimated_time": "5-11 minutes",
  "output_file": "/tmp/audio_conversion_a1b2/movie.web.mkv",
  "output_size_mb": 5234.5,
  "progress": {
    "status": "processing",
    "percentage": 45,
    "message": "Converting audio: 45%"
  },
  "created_at": "2026-02-16T05:00:00Z",
  "updated_at": "2026-02-16T05:02:30Z"
}
```

Status flow: `starting` → `processing` → `completed` | `error` | `cancelled`

## Frontend Implementation

### 1. Audio Converter Library
**File**: `/src/lib/audioConverter.ts`

Functions:

#### detectAudioCodec()
Local detection using ffmpeg.wasm (fast, no upload)
```typescript
const audioInfo = await detectAudioCodec(file, (progress, msg) => {
  console.log(`${progress}%: ${msg}`);
});
```

#### ensureCompatibleAudio()
Smart conversion router:
- Files ≤2GB: Local conversion (ffmpeg.wasm)
- Files >2GB: Server conversion (no memory limits)

```typescript
const result = await ensureCompatibleAudio(file, (progress, msg) => {
  setProgress(progress);
  setMessage(msg);
});

if (result.converted) {
  // Use result.file (converted)
} else {
  // Use original file (already compatible)
}
```

#### convertAudioOnServer()
Server-side conversion with polling
```typescript
const convertedFile = await convertAudioOnServer(file, (progress, msg) => {
  setProgress(progress);
  setMessage(msg);
});
```

Flow:
1. Upload file → get job_id
2. Poll /convert-audio-status/{job_id} every 2s
3. When status = completed → download file
4. Return as File object

### 2. Video Analysis UI
**File**: `/src/components/panels/VideoAnalysis.tsx`

Improvements:
- Progress bar for conversion
- Real-time progress updates
- File size warnings
- Estimated time display
- Better error handling

UI shows:
```
🔄 A converter áudio...
Conversão de áudio AC3 → AAC: 45%

[████████████░░░░░░░░░░] 45%

Ficheiros grandes podem demorar alguns minutos.
Não feche esta janela.
```

## Usage Example

### 1. User loads large MKV file (5.6GB)
```typescript
// VideoAnalysis.tsx
const handleFileSelect = async (file) => {
  // Quick check
  const check = await ensureCompatibleAudio(file, updateUI, true);

  if (check.audioInfo && !check.audioInfo.isCompatible) {
    const fileSizeGB = file.size / (1024**3);

    if (fileSizeGB > 2) {
      // Warn user about time
      const confirmed = confirm(
        `Áudio ${check.audioInfo.codec} incompatível\n` +
        `Ficheiro: ${fileSizeGB.toFixed(1)}GB\n` +
        `Tempo estimado: 5-11 minutos\n\n` +
        `Converter agora?`
      );

      if (!confirmed) {
        // Load without sound
        return;
      }
    }
  }

  // Convert (automatically uses server for >2GB)
  const result = await ensureCompatibleAudio(file, updateUI);

  if (result.converted) {
    toast.success('Áudio convertido com sucesso!');
    loadVideo(result.file);
  }
};
```

### 2. Server processes conversion
```python
# Background thread
def _convert_background(job_id, input_path, output_path):
    def progress(data):
        job_storage.update_job(job_id, {'progress': data})

    success = AudioConversionService.convert_audio_to_aac(
        input_path,
        output_path,
        progress_callback=progress
    )

    if success:
        job_storage.update_job(job_id, {
            'status': 'completed',
            'output_file': str(output_path)
        })
```

### 3. Frontend polls and downloads
```typescript
// Poll every 2s
while (true) {
  const status = await fetch(`/convert-audio-status/${jobId}`);

  if (status.status === 'completed') {
    // Download
    const file = await fetch(`/convert-audio-download/${jobId}`);
    return new File([await file.blob()], filename);
  }

  // Update UI
  setProgress(status.progress.percentage);
  setMessage(status.progress.message);

  await sleep(2000);
}
```

## Performance

### Conversion Speed
- ~1-2 minutes per GB (typical)
- 5.6GB file: 5-11 minutes
- No browser memory limits
- Uses server CPU (2 cores, 2Gi RAM)

### Optimization
- Copy video stream (no re-encoding): `-c:v copy`
- Convert only audio to AAC: `-c:a aac`
- Preserve subtitles: `-c:s copy`
- Map all streams: `-map 0`

## Error Handling

### Common Errors

1. **File too large for upload**
   - Solution: Increase Cloud Run max request size
   - Current: 32MB default, extended via timeout

2. **Conversion timeout**
   - Solution: Increase Cloud Run timeout
   - Current: 300s (5 minutes)
   - Recommendation: 600s for very large files

3. **Out of memory**
   - Solution: Increase Cloud Run memory
   - Current: 2Gi
   - Recommendation: 4Gi for 10GB+ files

4. **Job not found**
   - Cause: Job expired or deleted
   - Solution: Retry conversion

### Frontend Error Messages
```typescript
try {
  const result = await convertAudioOnServer(file, updateUI);
} catch (error) {
  if (error.message.includes('timeout')) {
    toast.error('Conversão demorou muito. Tente ficheiro menor.');
  } else if (error.message.includes('memory')) {
    toast.error('Ficheiro muito grande para conversão.');
  } else {
    toast.error('Falha na conversão. Tente novamente.');
  }
}
```

## Deployment

### Backend
```bash
cd /subtitle-translator
./deploy.sh production
```

Deployed to: `https://scriptum-v2-5-315653817267.europe-west1.run.app`

### Frontend
Update API_BASE in constants:
```typescript
// src/lib/constants.ts
export const API_BASE =
  'https://scriptum-v2-5-315653817267.europe-west1.run.app';
```

## Testing

### Test Audio Detection
```bash
curl -X POST \
  -F "video=@test.mkv" \
  https://scriptum-v2-5-315653817267.europe-west1.run.app/detect-audio-codec
```

### Test Conversion
```bash
# Start job
JOB_ID=$(curl -X POST -F "video=@test.mkv" \
  https://scriptum-v2-5-315653817267.europe-west1.run.app/convert-audio-mkv \
  | jq -r '.job_id')

# Check status
curl https://scriptum-v2-5-315653817267.europe-west1.run.app/convert-audio-status/$JOB_ID

# Download when complete
curl -O https://scriptum-v2-5-315653817267.europe-west1.run.app/convert-audio-download/$JOB_ID
```

## Monitoring

### View Logs
```bash
gcloud run services logs read scriptum-v2-5 --region=europe-west1
```

### Check Job Status
```bash
# In Firestore console
Collection: translation_jobs
Document: {job_id}
```

### Performance Metrics
- Cloud Run Metrics
- Request latency
- Memory usage
- CPU utilization

## Future Improvements

1. **Streaming upload** for very large files
2. **Resume support** for interrupted conversions
3. **Batch conversion** for multiple files
4. **Quality selection** (128k, 192k, 256k AAC bitrate)
5. **Progress via WebSocket** instead of polling
6. **Auto-cleanup** of old jobs (>7 days)

## References

- FFmpeg docs: https://ffmpeg.org/documentation.html
- Cloud Run: https://cloud.google.com/run/docs
- Firestore: https://cloud.google.com/firestore/docs
- ffmpeg.wasm: https://ffmpegwasm.netlify.app/
