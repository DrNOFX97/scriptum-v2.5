# Scriptum API v2.5

> Professional subtitle management backend with Flask + React frontend

Clean, modular API for video analysis, subtitle search, synchronization, and translation using service-oriented architecture with dependency injection.

---

## 🚀 Features

### Video Processing
- ✅ Video metadata extraction (codec, resolution, fps, duration)
- ✅ MKV to MP4 remuxing (instant, no re-encoding)
- ✅ Video format conversion with quality presets
- ✅ MKV subtitle track extraction

### Subtitle Management
- ✅ Multi-source subtitle search (OpenSubtitles + LegendasDivx)
- ✅ Automatic subtitle download
- ✅ MLX Whisper-based synchronization
- ✅ Google Gemini translation with context
- ✅ Subtitle validation and formatting

### Movie Recognition
- ✅ TMDB integration for metadata
- ✅ Automatic recognition from filename
- ✅ IMDB ID support

### Production Features
- ✅ Professional structured logging
- ✅ Automatic file cleanup
- ✅ Dependency injection for testability
- ✅ Standardized API responses
- ✅ Input validation decorators
- ✅ Comprehensive error handling

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- FFmpeg (for video processing)
- MLX Whisper (for subtitle sync)

### Backend Setup

\`\`\`bash
cd subtitle-translator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run server
python app.py
\`\`\`

Server starts at: http://localhost:5001

---

## 🏗️ Architecture

Backend uses service-oriented architecture with dependency injection:
- **Flask app factory** for testability
- **Blueprint-based routes** for modularity
- **Service layer** for business logic
- **Utility modules** for shared functionality

See full documentation in README for details.

---

## 🧪 Testing

\`\`\`bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/scriptum_api
\`\`\`

Current coverage: **25%** and growing

---

## 📄 License

MIT License

**Made with ❤️ by the Scriptum Team**
