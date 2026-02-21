# Scriptum API v2.5 - Architecture Documentation

## 📐 Overview

Scriptum API is a subtitle processing service built with Flask, following a clean service-oriented architecture with dependency injection.

## 🏗️ Architecture Pattern

```
┌─────────────────────────────────────────┐
│         WSGI Entry Point                │
│         (wsgi_prod.py)                  │
│  - Minimal wrapper                      │
│  - Production config                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Application Factory                │
│      (src/scriptum_api/app.py)          │
│  - create_app()                         │
│  - Service initialization               │
│  - Blueprint registration               │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌─────────────┐   ┌─────────────┐
│  Services   │   │   Routes    │
│  Container  │   │  (Blueprints)│
└─────────────┘   └─────────────┘
      │                 │
      │                 │
┌─────▼─────────────────▼─────┐
│  Individual Services        │
│  - OpenSubtitles           │
│  - LegendasDivx            │
│  - TMDB (Movie DB)         │
│  - Gemini (Translation)    │
│  - Video Processing        │
└────────────────────────────┘
```

## 📁 Directory Structure

```
subtitle-translator/
├── src/
│   └── scriptum_api/
│       ├── __init__.py
│       ├── app.py                  # Application factory
│       ├── config.py               # Configuration
│       ├── dependencies.py         # Service container
│       ├── constants.py            # Constants
│       ├── routes/                 # Route blueprints
│       │   ├── health.py
│       │   ├── subtitles.py
│       │   ├── video.py
│       │   ├── sync.py
│       │   ├── translation.py
│       │   └── config.py
│       ├── services/               # Business logic
│       │   ├── opensubtitles_service.py
│       │   ├── legendasdivx_service.py
│       │   ├── tmdb_service.py
│       │   ├── gemini_service.py
│       │   └── video_service.py
│       └── utils/                  # Utilities
│           ├── logger.py
│           ├── validators.py
│           ├── cleanup.py
│           └── storage.py
├── wsgi_prod.py                   # WSGI entry point (38 lines)
├── Dockerfile                      # Container definition
├── requirements.txt                # Python dependencies
├── deploy.sh                       # Automated deployment
└── .gcloudignore                  # Build optimization
```

## 🔧 Key Components

### 1. Application Factory (`app.py`)

The `create_app()` function follows the **Factory Pattern**, allowing flexible app creation for different environments:

```python
def create_app(config: Optional[Config] = None, upload_folder: Optional[Path] = None) -> Flask:
    """Create and configure Flask application"""
    # Initialize config
    # Setup CORS
    # Initialize services
    # Register blueprints
    # Start cleanup manager
    return app
```

**Benefits:**
- Testability (easy to create test instances)
- Environment flexibility (dev/staging/production)
- Clean separation of concerns

### 2. Service Container (`dependencies.py`)

Uses **Dependency Injection** pattern for loose coupling:

```python
@dataclass
class ServiceContainer:
    config: Config
    subtitle_service: Optional[OpenSubtitlesService]
    legendasdivx_service: Optional[LegendasDivxService]
    tmdb_service: Optional[TMDBService]
    gemini_service: Optional[GeminiService]
    video_service: Optional[VideoService]
```

**Benefits:**
- Services fail independently (graceful degradation)
- Easy to mock for testing
- Clear dependencies

### 3. Route Blueprints (`routes/`)

Each domain has its own blueprint:

```python
def create_subtitles_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """Create subtitle routes with injected dependencies"""
    bp = Blueprint('subtitles', __name__)

    @bp.route('/search-subtitles', methods=['POST'])
    def search_subtitles():
        # Use services.subtitle_service
        # Use services.legendasdivx_service
        pass

    return bp
```

**Benefits:**
- Modular routes
- Dependency injection at route level
- Easy to add/remove features

### 4. Services (`services/`)

Each external integration is a separate service:

#### OpenSubtitles Service
- Search subtitles
- Download subtitles
- Authentication handling

#### LegendasDivx Service
- Portuguese subtitle search
- RAR extraction (using `unar`)
- Encoding conversion (ISO-8859-1 → UTF-8)

#### TMDB Service
- Movie recognition from filename
- Metadata retrieval

#### Gemini Service
- Context-aware translation
- Tone adaptation

#### Video Service
- Video analysis
- Format conversion
- Subtitle extraction from MKV

## 🚀 Deployment

### Automated Deployment

```bash
./deploy.sh production
```

The script:
1. ✅ Checks prerequisites
2. 🏗️ Builds Docker image (Cloud Build)
3. 🚀 Deploys to Cloud Run
4. 🧪 Tests deployment
5. 📊 Shows logs and monitoring links

### Manual Deployment

```bash
# 1. Build image
gcloud builds submit --tag gcr.io/ligafaro-8000/scriptum-v2-5:latest

# 2. Deploy to Cloud Run
gcloud run deploy scriptum-v2-5 \
  --image gcr.io/ligafaro-8000/scriptum-v2-5:latest \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

## 🔐 Configuration

Configuration is managed through environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENSUBTITLES_API_KEY` | OpenSubtitles API key | ✅ |
| `TMDB_API_KEY` | TMDB API key | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ❌ |
| `LEGENDASDIVX_API_URL` | LegendasDivx API endpoint | ❌ |
| `PORT` | Server port (default: 8080) | ❌ |
| `DEBUG` | Debug mode (default: false) | ❌ |
| `CORS_ORIGINS` | CORS origins (default: *) | ❌ |
| `PRODUCTION_CORS` | Enable production CORS (default: true) | ❌ |

## 📊 Service Availability

The API uses **graceful degradation** - if a service fails to load, the API continues working with reduced functionality:

```
🚀 App created with 5 services loaded
✅ ConfigService
✅ OpenSubtitlesService
✅ LegendasDivxService
✅ TMDBService
⚠️  GeminiService (API key not configured)
```

## 🧪 Testing

### Health Check
```bash
curl https://scriptum-v2-5-315653817267.europe-west1.run.app/health
```

### Search Subtitles
```bash
curl -X POST https://scriptum-v2-5-315653817267.europe-west1.run.app/search-subtitles \
  -H 'Content-Type: application/json' \
  -d '{"query": "The Matrix", "language": "pt-PT"}'
```

### Download Subtitle
```bash
curl -X POST https://scriptum-v2-5-315653817267.europe-west1.run.app/download-subtitle \
  -H 'Content-Type: application/json' \
  -d '{"file_id": "123456", "source": "legendasdivx"}'
```

## 🔍 Monitoring

### View Logs
```bash
gcloud run services logs read scriptum-v2-5 --region=europe-west1 --limit=50
```

### View Service Details
```bash
gcloud run services describe scriptum-v2-5 --region=europe-west1
```

### Cloud Console
https://console.cloud.google.com/run/detail/europe-west1/scriptum-v2-5

## 🐛 Troubleshooting

### Service Not Loading

Check logs for initialization errors:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=scriptum-v2-5" --limit=100
```

### CORS Issues

Verify CORS environment variable:
```bash
gcloud run services describe scriptum-v2-5 --region=europe-west1 --format='value(spec.template.spec.containers[0].env)'
```

### Missing Dependencies

The Docker image includes:
- `ffmpeg` - Video processing
- `unar` - RAR extraction
- `rarfile` - Python RAR library

Verify in Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    unar \
    && rm -rf /var/lib/apt/lists/*
```

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/diagnostics` | GET | Configuration diagnostics |
| `/search-subtitles` | POST | Search subtitles (OpenSubtitles + LegendasDivx) |
| `/download-subtitle` | POST | Download subtitle file |
| `/download/<filename>` | GET | Serve downloaded file |
| `/recognize-movie` | POST | Recognize movie from filename |
| `/analyze-video` | POST | Analyze video metadata |
| `/extract-mkv-subtitles` | POST | Extract embedded subtitles |
| `/sync` | POST | Sync subtitles to video |
| `/translate` | POST | Translate subtitles |
| `/config` | GET/POST | Get/update configuration |

## 🎯 Best Practices

1. **Keep wsgi_prod.py minimal** - It's just a wrapper
2. **Use service container** - Don't access services directly
3. **Handle service failures gracefully** - Check if service exists
4. **Use environment variables** - Never hardcode credentials
5. **Follow blueprint pattern** - One blueprint per domain
6. **Test locally first** - Use `python wsgi_prod.py`
7. **Use automated deployment** - `./deploy.sh production`

## 🔄 Development Workflow

1. Make changes to code
2. Test locally: `python wsgi_prod.py`
3. Run automated deployment: `./deploy.sh`
4. Monitor logs: `gcloud run services logs read scriptum-v2-5 --region=europe-west1`
5. Verify health check: `curl https://scriptum-v2-5-315653817267.europe-west1.run.app/health`

## 📝 Recent Improvements

- ✅ Simplified wsgi_prod.py from 300+ lines to 38 lines
- ✅ Added configurable CORS support
- ✅ Created automated deployment script
- ✅ Added LegendasDivx RAR extraction support
- ✅ Improved service container with graceful degradation
- ✅ Added comprehensive logging
- ✅ Created .gcloudignore for faster builds (138 MB vs 1.9 GB)

---

Last updated: 2026-02-15
