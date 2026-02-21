#!/usr/bin/env python3
"""
Scriptum Sync API Server v2.0
Servidor Flask para sincronização automática via web interface
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
from pathlib import Path
import sys
import subprocess
import os

app = Flask(__name__)
CORS(app)

# Importar funções do smart_sync
sys.path.insert(0, str(Path(__file__).parent))
from smart_sync import (
    get_video_framerate,
    detect_srt_framerate,
    convert_framerate,
    get_video_duration,
    analyze_sync,
    apply_offset
)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'version': '2.0', 'service': 'Scriptum Sync API'})


@app.route('/sync', methods=['POST'])
def sync_subtitles():
    """
    Sincroniza legendas automaticamente

    Expects multipart/form-data with:
    - video: video file
    - subtitle: .srt file

    Returns JSON with offset and quality metrics
    """

    if 'video' not in request.files or 'subtitle' not in request.files:
        return jsonify({'error': 'Missing video or subtitle file'}), 400

    video_file = request.files['video']
    subtitle_file = request.files['subtitle']

    if not subtitle_file.filename.endswith('.srt'):
        return jsonify({'error': 'Subtitle must be .srt format'}), 400

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Save uploaded files
        video_path = tmp / video_file.filename
        srt_original = tmp / subtitle_file.filename

        video_file.save(str(video_path))
        subtitle_file.save(str(srt_original))

        try:
            print(f"📹 Processing: {video_file.filename}")
            print(f"📄 Subtitle: {subtitle_file.filename}")

            # Step 1: Analyze framerates
            print("📊 Analyzing framerates...")
            video_fps = get_video_framerate(video_path)
            srt_fps = detect_srt_framerate(srt_original)

            work_file = tmp / 'work.srt'
            fps_diff = abs(video_fps - srt_fps) if srt_fps else 0

            # Step 2: Convert framerate if needed
            if fps_diff > 0.5:
                print(f"🔧 Converting framerate: {srt_fps} → {video_fps} fps")
                convert_framerate(srt_original, srt_fps, video_fps, work_file)
            else:
                import shutil
                shutil.copy(srt_original, work_file)

            # Step 3: Get video duration
            print("📏 Getting video duration...")
            duration = get_video_duration(video_path)

            # Step 4: Detect audio language
            print("🎙️  Detecting audio language...")
            import mlx_whisper
            audio_sample = tmp / 'sample.wav'
            subprocess.run([
                'ffmpeg', '-y', '-ss', '60', '-t', '30',
                '-i', str(video_path), '-ac', '1', '-ar', '16000',
                str(audio_sample)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            result = mlx_whisper.transcribe(
                str(audio_sample),
                path_or_hf_repo='mlx-community/whisper-tiny'
            )
            detected_lang = result.get('language', 'en')
            print(f"   ✅ Language: {detected_lang}")

            # Step 5: Analyze synchronization
            print("🔍 Analyzing synchronization...")
            offsets, avg_offset, std_dev = analyze_sync(
                work_file, video_path, duration, num_samples=5, language=detected_lang
            )

            if offsets is None:
                return jsonify({'error': 'Failed to analyze synchronization'}), 500

            print(f"   📊 Offset: {avg_offset:+.2f}s (σ={std_dev:.2f}s)")

            # Step 6: Apply correction
            if abs(avg_offset) > 0.2:
                print(f"🔧 Applying correction: {avg_offset:+.2f}s")
                apply_offset(work_file, avg_offset, work_file)

            # Step 7: Save result
            print("💾 Saving result...")
            output_file = tmp / (srt_original.stem + '.sync.srt')
            import shutil
            shutil.move(work_file, output_file)

            # Read synced subtitle content
            with open(output_file, 'r', encoding='utf-8') as f:
                synced_content = f.read()

            print("✅ Synchronization complete!")

            # Return results
            return jsonify({
                'success': True,
                'offset': round(avg_offset, 2),
                'std_dev': round(std_dev, 2),
                'offsets': [round(o, 2) for o in offsets],
                'video_fps': video_fps,
                'subtitle_fps': srt_fps,
                'framerate_converted': fps_diff > 0.5,
                'language': detected_lang,
                'duration': int(duration),
                'synced_content': synced_content,
                'filename': output_file.name
            })

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


@app.route('/search-subtitles', methods=['POST'])
def search_subtitles():
    """
    Busca legendas no OpenSubtitles ou Subscene (fallback)

    Expects JSON or multipart/form-data:
    - video: video file (optional, for hash search)
    - query: movie name (optional)
    - imdb_id: IMDB ID (optional)
    - language: preferred language (default: 'pt')

    Returns JSON with subtitle list
    """
    # Try OpenSubtitles (requires API key)
    try:
        from opensubtitles_api import OpenSubtitlesAPI
        api = OpenSubtitlesAPI()
        print("✅ Using OpenSubtitles API")
    except (ValueError, Exception) as e:
        # No API key configured
        error_msg = str(e)
        print(f"❌ OpenSubtitles API key not configured: {error_msg}")

        return jsonify({
            'success': False,
            'error': 'OpenSubtitles API key required',
            'message': 'Para usar a busca de legendas, é necessário configurar uma API key do OpenSubtitles.com (gratuita)',
            'instructions': {
                'step1': 'Crie uma conta gratuita em https://www.opensubtitles.com',
                'step2': 'Vá para https://www.opensubtitles.com/api e gere uma API key',
                'step3': 'Defina a variável de ambiente: export OPENSUBTITLES_API_KEY="sua_chave"',
                'step4': 'Reinicie o servidor: venv/bin/python sync_api.py',
                'limit': 'Conta gratuita permite 20 downloads por dia'
            }
        }), 403

    language = request.form.get('language', 'pt') if request.files else request.json.get('language', 'pt')
    data = request.json if not request.files else request.form
    subtitles = []

    # Try hash search if video provided (most accurate)
    if 'video' in request.files:
        video_file = request.files['video']
        with tempfile.TemporaryDirectory() as tmp:
            video_path = Path(tmp) / video_file.filename
            video_file.save(str(video_path))

            print(f"🔍 Searching by video hash...")
            subtitles = api.search_by_hash(str(video_path), languages=[language, 'en'])

    # Try IMDB ID search
    if not subtitles:
        imdb_id = data.get('imdb_id')
        if imdb_id:
            print(f"🔍 Searching by IMDB ID: {imdb_id}...")
            subtitles = api.search_by_imdb_id(imdb_id, languages=[language, 'en'])

    # Try query search
    if not subtitles:
        query = data.get('query')
        year = data.get('year')
        if query:
            print(f"🔍 Searching by query: {query}...")
            subtitles = api.search_by_query(query, year=year, languages=[language, 'en'])

    if not subtitles:
        return jsonify({'success': False, 'message': 'No subtitles found'}), 404

    # Format results
    results = [api.format_subtitle_info(sub) for sub in subtitles[:20]]
    print(f"✅ Found {len(results)} subtitles")

    return jsonify({
        'success': True,
        'count': len(results),
        'subtitles': results,
        'source': 'opensubtitles'
    })


@app.route('/download-subtitle', methods=['POST'])
def download_subtitle_endpoint():
    """
    Download subtitle from OpenSubtitles

    Expects JSON: { "file_id": "12345" }
    Returns subtitle content
    """
    data = request.json
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({'error': 'Missing file_id'}), 400

    try:
        from opensubtitles_api import OpenSubtitlesAPI
        api = OpenSubtitlesAPI()

        print(f"💾 Downloading from OpenSubtitles: {file_id}...")

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / f"subtitle_{file_id}.srt"
            downloaded = api.download_subtitle(file_id, str(output_path))

            # Read content
            with open(downloaded, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"✅ Subtitle downloaded: {len(content)} bytes")

            return jsonify({
                'success': True,
                'content': content,
                'filename': f'opensubtitles_{file_id}.srt'
            })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/recognize', methods=['POST'])
def recognize_movie():
    """
    Reconhece filme pelo nome do arquivo

    Expects JSON: { "filename": "movie.mkv" }
    Returns TMDB movie data
    """
    data = request.json
    if 'filename' not in data:
        return jsonify({'error': 'Missing filename'}), 400

    import re
    import requests

    filename = data['filename']

    # Extract clean movie name
    clean_name = re.sub(r'\.(mp4|mkv|avi|webm)$', '', filename, flags=re.IGNORECASE)
    clean_name = re.sub(r'[\._]', ' ', clean_name)
    clean_name = re.sub(r'\d{4}.*$', '', clean_name)
    clean_name = re.sub(r'\b(720p|1080p|2160p|BluRay|WEB-DL|HDTV|x264|x265|HEVC)\b.*', '', clean_name, flags=re.IGNORECASE)
    clean_name = clean_name.strip()

    print(f"🔍 Searching for: {clean_name}")

    # Use TMDB API
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', '8d6d91941230817f7807d643736e8a49')  # Demo key

    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/search/movie',
            params={'query': clean_name, 'api_key': TMDB_API_KEY}
        )

        if response.status_code == 200:
            data = response.json()
            if data['results']:
                movie = data['results'][0]
                print(f"   ✅ Found: {movie['title']}")
                return jsonify({
                    'success': True,
                    'movie': {
                        'title': movie['title'],
                        'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                        'rating': movie.get('vote_average', 0),
                        'poster': f"https://image.tmdb.org/t/p/w200{movie['poster_path']}" if movie.get('poster_path') else None,
                        'overview': movie.get('overview', '')
                    }
                })
            else:
                print("   ⚠️  Movie not found")
                return jsonify({'success': False, 'message': 'Movie not found'}), 404
        else:
            return jsonify({'error': 'TMDB API error'}), 500

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    """
    Analisa vídeo e retorna informações completas:
    - Metadados do filme (TMDB)
    - Legendas disponíveis (OpenSubtitles)
    - Informações do arquivo (formato, duração, tamanho)

    Expects multipart/form-data with:
    - video: video file
    - language: preferred subtitle language (default: 'pt')

    Returns comprehensive JSON with all available info
    """
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']
    language = request.form.get('language', 'pt')

    print(f"\n{'='*70}")
    print(f"🎬 Analyzing video: {video_file.filename}")
    print(f"{'='*70}")

    result = {
        'success': True,
        'filename': video_file.filename,
        'movie': None,
        'subtitles': [],
        'video_info': {},
        'can_convert_to_mp4': False
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / video_file.filename
        video_file.save(str(video_path))

        # 1. Get video file info
        print("\n📊 Analyzing video file...")
        try:
            file_ext = video_path.suffix.lower()
            file_size = video_path.stat().st_size

            # Get video metadata with ffprobe
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ], capture_output=True, text=True, check=True)

            import json
            metadata = json.loads(probe_result.stdout)

            duration = float(metadata['format'].get('duration', 0))
            video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)

            result['video_info'] = {
                'format': file_ext[1:].upper(),
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'duration': int(duration),
                'duration_formatted': f"{int(duration//3600)}h {int((duration%3600)//60)}m" if duration >= 3600 else f"{int(duration//60)}m {int(duration%60)}s",
                'codec': video_stream.get('codec_name', 'unknown') if video_stream else 'unknown',
                'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}" if video_stream else 'unknown',
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream and 'r_frame_rate' in video_stream else 0
            }

            # Check if conversion to MP4 is needed/possible
            result['can_convert_to_mp4'] = file_ext in ['.mkv', '.avi', '.webm', '.flv', '.wmv']

            print(f"   ✅ Format: {result['video_info']['format']}")
            print(f"   ✅ Size: {result['video_info']['size_mb']} MB")
            print(f"   ✅ Duration: {result['video_info']['duration_formatted']}")
            print(f"   ✅ Resolution: {result['video_info']['resolution']}")

        except Exception as e:
            print(f"   ⚠️  Could not analyze video: {str(e)}")

        # 2. Recognize movie from filename
        print("\n🎬 Recognizing movie...")
        try:
            import re
            import requests

            filename = video_file.filename
            print(f"   📝 Filename: {filename}")

            # Extract clean name
            clean_name = re.sub(r'\.(mp4|mkv|avi|webm|mov|flv|wmv)$', '', filename, flags=re.IGNORECASE)
            clean_name = re.sub(r'[\._]', ' ', clean_name)

            # Extract year
            year_match = re.search(r'(19|20)\d{2}', clean_name)
            year = year_match.group(0) if year_match else None

            # Remove everything after year
            clean_name = re.sub(r'\d{4}.*$', '', clean_name)

            # Remove quality/codec/release info
            clean_name = re.sub(r'\b(720p|1080p|2160p|4K|BluRay|WEB-DL|WEBRip|HDTV|x264|x265|HEVC|AAC|AAC5\.1|10bits|DTS|AMZN|Rapta)\b.*', '', clean_name, flags=re.IGNORECASE)
            clean_name = clean_name.strip()

            print(f"   🔍 Searching: '{clean_name}' (year: {year or 'any'})")

            TMDB_API_KEY = os.getenv('TMDB_API_KEY', '8d6d91941230817f7807d643736e8a49')

            # Try search by name first
            params = {'query': clean_name, 'api_key': TMDB_API_KEY}
            if year:
                params['year'] = year

            response = requests.get(
                f'https://api.themoviedb.org/3/search/movie',
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    movie = data['results'][0]
                    result['movie'] = {
                        'title': movie['title'],
                        'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                        'rating': movie.get('vote_average', 0),
                        'poster': f"https://image.tmdb.org/t/p/w300{movie['poster_path']}" if movie.get('poster_path') else None,
                        'overview': movie.get('overview', ''),
                        'imdb_id': movie.get('imdb_id', None)
                    }
                    print(f"   ✅ Found: {movie['title']} ({result['movie']['year']})")
                    print(f"   ⭐ Rating: {result['movie']['rating']}/10")
                else:
                    # If not found by name, try by IMDB ID if it looks like one is in the filename
                    imdb_match = re.search(r'(tt\d{7,8})', filename)
                    if imdb_match:
                        imdb_id = imdb_match.group(1)
                        print(f"   🔍 Trying IMDB ID: {imdb_id}")

                        # TMDB find endpoint accepts IMDB IDs
                        find_response = requests.get(
                            f'https://api.themoviedb.org/3/find/{imdb_id}',
                            params={'api_key': TMDB_API_KEY, 'external_source': 'imdb_id'}
                        )

                        if find_response.status_code == 200:
                            find_data = find_response.json()
                            if find_data.get('movie_results'):
                                movie = find_data['movie_results'][0]
                                result['movie'] = {
                                    'title': movie['title'],
                                    'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                                    'rating': movie.get('vote_average', 0),
                                    'poster': f"https://image.tmdb.org/t/p/w300{movie['poster_path']}" if movie.get('poster_path') else None,
                                    'overview': movie.get('overview', ''),
                                    'imdb_id': imdb_id
                                }
                                print(f"   ✅ Found via IMDB: {movie['title']} ({result['movie']['year']})")
                                print(f"   ⭐ Rating: {result['movie']['rating']}/10")
                            else:
                                print(f"   ⚠️  Movie not found in TMDB")
                        else:
                            print(f"   ⚠️  Movie not found in TMDB")
                    else:
                        print(f"   ⚠️  Movie not found in TMDB")
            else:
                print(f"   ⚠️  TMDB API error: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Recognition failed: {str(e)}")

        # 3. Search for subtitles (quick search by movie name first)
        print("\n🔍 Searching for subtitles...")
        try:
            from opensubtitles_api import OpenSubtitlesAPI
            api = OpenSubtitlesAPI()

            subtitles = []

            # If we have movie info, try by query first (fastest)
            if result['movie']:
                query = f"{result['movie']['title']} {result['movie']['year']}"
                print(f"   🔍 Quick search: {query}")
                subtitles = api.search_by_query(query, languages=[language, 'en'])

            # Only do hash search if quick search failed (hash is slow)
            if not subtitles:
                print(f"   🔍 Hash search (slower)...")
                subtitles = api.search_by_hash(str(video_path), languages=[language, 'en'])

            if subtitles:
                result['subtitles'] = [api.format_subtitle_info(sub) for sub in subtitles[:20]]
                print(f"   ✅ Found {len(result['subtitles'])} subtitles")

                # Group by language
                by_lang = {}
                for sub in result['subtitles']:
                    lang = sub.get('language', 'unknown')
                    by_lang[lang] = by_lang.get(lang, 0) + 1

                for lang, count in by_lang.items():
                    print(f"      • {lang}: {count} subtitles")
            else:
                print(f"   ⚠️  No subtitles found")

        except Exception as e:
            print(f"   ⚠️  Subtitle search failed: {str(e)}")
            result['subtitles_error'] = str(e)

    print(f"{'='*70}\n")
    return jsonify(result)


@app.route('/quick-subtitle-search', methods=['POST'])
def quick_subtitle_search():
    """
    Busca rápida de legendas usando apenas o nome do arquivo
    Não requer upload do vídeo completo

    Expects JSON: { "filename": "movie.mkv", "language": "pt" }
    Returns subtitle list
    """
    data = request.json
    if 'filename' not in data:
        return jsonify({'error': 'Missing filename'}), 400

    filename = data['filename']
    language = data.get('language', 'pt')

    print(f"\n🔍 Quick subtitle search for: {filename}")

    try:
        from opensubtitles_api import OpenSubtitlesAPI
        import re
        import requests

        api = OpenSubtitlesAPI()

        # Extract clean movie name from filename
        clean_name = re.sub(r'\.(mp4|mkv|avi|webm|mov|flv|wmv)$', '', filename, flags=re.IGNORECASE)
        clean_name = re.sub(r'[\._]', ' ', clean_name)
        year_match = re.search(r'(19|20)\d{2}', clean_name)
        year = year_match.group(0) if year_match else None
        clean_name = re.sub(r'\d{4}.*$', '', clean_name)
        clean_name = re.sub(r'\b(720p|1080p|2160p|4K|BluRay|WEB-DL|HDTV|x264|x265|HEVC|AAC|DTS)\b.*', '', clean_name, flags=re.IGNORECASE)
        clean_name = clean_name.strip()

        print(f"   📝 Extracted name: {clean_name} ({year or 'no year'})")

        # Try TMDB first for better search
        movie_title = clean_name
        TMDB_API_KEY = os.getenv('TMDB_API_KEY', '8d6d91941230817f7807d643736e8a49')

        try:
            response = requests.get(
                f'https://api.themoviedb.org/3/search/movie',
                params={'query': clean_name, 'api_key': TMDB_API_KEY, 'year': year},
                timeout=3
            )
            if response.status_code == 200:
                tmdb_data = response.json()
                if tmdb_data['results']:
                    movie = tmdb_data['results'][0]
                    movie_title = movie['title']
                    movie_year = movie.get('release_date', '')[:4] if movie.get('release_date') else year
                    print(f"   🎬 TMDB: {movie_title} ({movie_year})")
        except:
            pass

        # Search subtitles
        query = f"{movie_title} {year or ''}"
        print(f"   🔍 Searching: {query}")

        subtitles = api.search_by_query(query.strip(), languages=[language, 'en'])

        if subtitles:
            results = [api.format_subtitle_info(sub) for sub in subtitles[:20]]
            print(f"   ✅ Found {len(results)} subtitles")

            return jsonify({
                'success': True,
                'count': len(results),
                'subtitles': results
            })
        else:
            print(f"   ⚠️  No subtitles found")
            return jsonify({
                'success': False,
                'message': 'No subtitles found'
            }), 404

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/extract-mkv-subtitles', methods=['POST'])
def extract_mkv_subtitles():
    """
    Extrai legendas embutidas de arquivos MKV

    Expects multipart/form-data with:
    - video: MKV file

    Returns JSON with list of extracted subtitle tracks
    """
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']

    print(f"\n{'='*70}")
    print(f"📤 Extracting subtitles from: {video_file.filename}")
    print(f"{'='*70}\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / video_file.filename
        video_file.save(str(video_path))

        try:
            # First, get subtitle track info
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-select_streams', 's', str(video_path)
            ], capture_output=True, text=True, check=True)

            import json
            metadata = json.loads(probe_result.stdout)
            subtitle_streams = metadata.get('streams', [])

            if not subtitle_streams:
                print("   ⚠️  No subtitle tracks found")
                return jsonify({
                    'success': False,
                    'message': 'No embedded subtitles found in MKV'
                }), 404

            print(f"   ✅ Found {len(subtitle_streams)} subtitle track(s)")

            extracted_subs = []

            for idx, stream in enumerate(subtitle_streams):
                stream_index = stream.get('index')
                codec = stream.get('codec_name', 'unknown')
                language = stream.get('tags', {}).get('language', 'unknown')
                title = stream.get('tags', {}).get('title', f'Track {idx+1}')

                # Only extract SRT-compatible formats
                if codec not in ['srt', 'subrip', 'ass', 'ssa']:
                    print(f"   ⚠️  Skipping track {idx+1} ({codec} not supported)")
                    continue

                output_filename = f"{video_path.stem}.{language}.{idx}.srt"
                output_path = tmp / output_filename

                print(f"   📥 Extracting track {idx+1}: {title} ({language}, {codec})")

                # Extract subtitle track
                extract_cmd = [
                    'ffmpeg', '-y', '-i', str(video_path),
                    '-map', f'0:{stream_index}',
                    '-c:s', 'srt',  # Convert to SRT
                    str(output_path)
                ]

                subprocess.run(
                    extract_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

                # Read extracted subtitle
                with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                extracted_subs.append({
                    'track_number': idx + 1,
                    'language': language,
                    'title': title,
                    'codec': codec,
                    'filename': output_filename,
                    'content': content,
                    'size': len(content)
                })

                print(f"      ✅ Extracted {len(content)} bytes")

            if not extracted_subs:
                return jsonify({
                    'success': False,
                    'message': 'No compatible subtitle tracks found (only SRT/ASS/SSA supported)'
                }), 404

            print(f"\n✅ Extraction complete: {len(extracted_subs)} subtitle(s)")
            print(f"{'='*70}\n")

            return jsonify({
                'success': True,
                'count': len(extracted_subs),
                'subtitles': extracted_subs
            })

        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e}")
            return jsonify({
                'error': 'Failed to extract subtitles',
                'details': str(e)
            }), 500
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


@app.route('/remux-mkv-to-mp4', methods=['POST'])
def remux_mkv_to_mp4():
    """
    Remux MKV to MP4 (copy streams without re-encoding - FAST!)
    Extrai o vídeo MP4/H.264 do container MKV sem re-codificar

    Expects multipart/form-data with:
    - video: MKV file

    Returns MP4 file (binary) or JSON error
    """
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']

    if not video_file.filename.lower().endswith('.mkv'):
        return jsonify({
            'error': 'Only MKV files supported',
            'message': 'This endpoint only works with MKV files'
        }), 400

    print(f"\n{'='*70}")
    print(f"🎞️  Remuxing MKV to MP4: {video_file.filename}")
    print(f"   (Sem re-codificação - apenas copia streams)")
    print(f"{'='*70}\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / video_file.filename
        output_filename = input_path.stem + '.mp4'
        output_path = tmp / output_filename

        video_file.save(str(input_path))

        try:
            # First, check what codecs are in the MKV
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', str(input_path)
            ], capture_output=True, text=True, check=True)

            import json
            metadata = json.loads(probe_result.stdout)

            video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
            audio_streams = [s for s in metadata['streams'] if s['codec_type'] == 'audio']

            if not video_stream:
                return jsonify({'error': 'No video stream found in MKV'}), 400

            video_codec = video_stream.get('codec_name', 'unknown')
            print(f"   📹 Video codec: {video_codec}")

            for idx, audio in enumerate(audio_streams):
                print(f"   🔊 Audio {idx+1}: {audio.get('codec_name', 'unknown')}")

            # Check if we can do a simple remux (no re-encoding needed)
            can_remux = video_codec in ['h264', 'hevc', 'mpeg4']

            if can_remux:
                print(f"   ✅ Codec compatível - fazendo remux (RÁPIDO)")

                # Simple remux - just copy streams (VERY FAST)
                cmd = [
                    'ffmpeg', '-y', '-i', str(input_path),
                    '-c', 'copy',  # Copy all streams without re-encoding
                    '-movflags', '+faststart',  # Optimize for web playback
                    str(output_path)
                ]
            else:
                print(f"   ⚠️  Codec {video_codec} não é compatível com MP4")
                return jsonify({
                    'error': 'Incompatible codec',
                    'message': f'Video codec {video_codec} cannot be directly copied to MP4. Use full conversion instead.',
                    'codec': video_codec,
                    'needs_conversion': True
                }), 400

            print(f"   🔄 Processando...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Get file sizes for comparison
            input_size = input_path.stat().st_size / (1024 * 1024)
            output_size = output_path.stat().st_size / (1024 * 1024)

            print(f"   ✅ Remux completo!")
            print(f"      Input:  {input_size:.2f} MB")
            print(f"      Output: {output_size:.2f} MB")
            print(f"      Time: Instant (no re-encoding)")
            print(f"{'='*70}\n")

            # Read remuxed file
            with open(output_path, 'rb') as f:
                remuxed_data = f.read()

            from flask import send_file
            import io

            return send_file(
                io.BytesIO(remuxed_data),
                mimetype='video/mp4',
                as_attachment=True,
                download_name=output_filename
            )

        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e.stderr}")
            return jsonify({
                'error': 'Remux failed',
                'details': e.stderr
            }), 500
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


@app.route('/convert-to-mp4', methods=['POST'])
def convert_to_mp4():
    """
    Converte vídeo para MP4 (H.264 + AAC)

    Expects multipart/form-data with:
    - video: video file to convert
    - quality: conversion quality (fast/balanced/high, default: balanced)

    Returns converted video or conversion status
    """
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']
    quality = request.form.get('quality', 'balanced')

    # Check if already MP4
    if video_file.filename.lower().endswith('.mp4'):
        return jsonify({
            'success': False,
            'message': 'File is already MP4 format'
        }), 400

    print(f"\n{'='*70}")
    print(f"🎞️  Converting to MP4: {video_file.filename}")
    print(f"   Quality preset: {quality}")
    print(f"{'='*70}\n")

    # Quality presets
    presets = {
        'fast': {'crf': 28, 'preset': 'veryfast'},
        'balanced': {'crf': 23, 'preset': 'medium'},
        'high': {'crf': 18, 'preset': 'slow'}
    }

    settings = presets.get(quality, presets['balanced'])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / video_file.filename
        output_filename = input_path.stem + '.mp4'
        output_path = tmp / output_filename

        video_file.save(str(input_path))

        try:
            # Convert with ffmpeg
            cmd = [
                'ffmpeg', '-y', '-i', str(input_path),
                '-c:v', 'libx264',
                '-crf', str(settings['crf']),
                '-preset', settings['preset'],
                '-c:a', 'aac',
                '-b:a', '192k',
                '-movflags', '+faststart',
                str(output_path)
            ]

            print("🔄 Converting... (this may take a while)")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Get file sizes for comparison
            input_size = input_path.stat().st_size / (1024 * 1024)
            output_size = output_path.stat().st_size / (1024 * 1024)

            print(f"✅ Conversion complete!")
            print(f"   Input:  {input_size:.2f} MB")
            print(f"   Output: {output_size:.2f} MB")
            print(f"   Ratio:  {(output_size/input_size)*100:.1f}%")
            print(f"{'='*70}\n")

            # Read converted file
            with open(output_path, 'rb') as f:
                converted_data = f.read()

            from flask import send_file
            import io

            return send_file(
                io.BytesIO(converted_data),
                mimetype='video/mp4',
                as_attachment=True,
                download_name=output_filename
            )

        except subprocess.CalledProcessError as e:
            print(f"❌ Conversion failed: {e.stderr}")
            return jsonify({
                'error': 'Conversion failed',
                'details': e.stderr
            }), 500
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({'error': str(e)}), 500


@app.route('/translate', methods=['POST'])
def translate_subtitle():
    """
    Traduz legendas SRT usando Google Gemini

    Expects multipart/form-data with:
    - subtitle: .srt file
    - source_lang: source language (en, pt)
    - target_lang: target language (en, pt)
    - movie_context: optional movie name for context

    Returns translated SRT file
    """
    if 'subtitle' not in request.files:
        return jsonify({'error': 'Missing subtitle file'}), 400

    subtitle_file = request.files['subtitle']
    source_lang = request.form.get('source_lang', 'en')
    target_lang = request.form.get('target_lang', 'pt')
    movie_context = request.form.get('movie_context', '')

    print(f"\n{'='*70}")
    print(f"🌐 Translating subtitle: {subtitle_file.filename}")
    print(f"   {source_lang.upper()} → {target_lang.upper()}")
    if movie_context:
        print(f"   Context: {movie_context}")
    print(f"{'='*70}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / subtitle_file.filename
        subtitle_file.save(str(input_path))

        try:
            # Import translation module
            from translate import SRTParser, GeminiTranslator, SubtitleValidator

            # Read original
            print("📖 Reading subtitle file...")
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse
            print("🔍 Parsing subtitles...")
            original_subs = SRTParser.parse(content)
            print(f"✅ {len(original_subs)} subtitles found")

            # Translate
            print(f"🌐 Translating {len(original_subs)} subtitles...")
            gemini_api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCl8KmWN8aE1o9gX1BzE8SJpdmzF21tp2c')
            translator = GeminiTranslator(gemini_api_key)

            # Custom batch translation with progress updates
            translated_subs = []
            batch_size = 10
            total_batches = (len(original_subs) + batch_size - 1) // batch_size

            for i in range(0, len(original_subs), batch_size):
                batch = original_subs[i:i + batch_size]
                batch_num = i // batch_size + 1

                print(f"   Batch {batch_num}/{total_batches} ({int((i / len(original_subs)) * 100)}%)")

                # Translate batch
                translated_batch = translator._translate_texts(batch)
                translated_subs.extend(translated_batch)

            print(f"✅ Translation complete: {len(translated_subs)} subtitles")

            # Validate
            print("🔍 Validating translation...")
            validator = SubtitleValidator()
            issues = validator.validate(original_subs, translated_subs)

            # Auto-fix line breaks
            if issues['line_rule_violations']:
                print(f"🔧 Applying line rules to {len(issues['line_rule_violations'])} subtitles...")
                translated_subs = validator.fix_line_breaks(original_subs, translated_subs)

            # Generate output
            output_content = SRTParser.generate(translated_subs)

            print(f"✅ Translation successful!")
            print(f"{'='*70}\n")

            # Return as file
            from flask import send_file
            import io

            output_filename = subtitle_file.filename.replace('.srt', f'_{target_lang}.srt')

            return send_file(
                io.BytesIO(output_content.encode('utf-8')),
                mimetype='text/plain',
                as_attachment=True,
                download_name=output_filename
            )

        except Exception as e:
            print(f"❌ Translation error: {str(e)}")
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("🎬 Scriptum Sync API Server v2.0")
    print("=" * 70)
    print("\nEndpoints:")
    print("  GET  /health                  - Health check")
    print("  POST /sync                    - Sincronizar legendas (multipart/form-data)")
    print("  POST /recognize               - Reconhecer filme (JSON)")
    print("  POST /search-subtitles        - Buscar legendas OpenSubtitles")
    print("  POST /download-subtitle       - Download legenda OpenSubtitles")
    print("  POST /quick-subtitle-search   - Busca rápida sem upload (JSON) ⚡")
    print("  POST /analyze-video           - Análise completa de vídeo (multipart/form-data)")
    print("  POST /extract-mkv-subtitles   - Extrair legendas do MKV (multipart/form-data) 📤")
    print("  POST /remux-mkv-to-mp4        - Remux MKV → MP4 (sem re-encoding, instantâneo) ⚡")
    print("  POST /convert-to-mp4          - Converter vídeo para MP4 (multipart/form-data)")
    print("  POST /translate               - Traduzir legendas (EN↔PT) com Google Gemini 🌐")
    print("\nServidor em: http://localhost:5001")
    print("\n⚠️  Nota: OpenSubtitles requer OPENSUBTITLES_API_KEY")
    print("   Obtenha chave gratuita em: https://www.opensubtitles.com/api")
    print("=" * 70 + "\n")

    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
