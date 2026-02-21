"""
Sync service
Handles subtitle synchronization using MLX Whisper with existing smart_sync.py module
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import subprocess

# Import existing sync module (now in utils)
from ..utils.sync_utils import (
    get_video_framerate,
    detect_srt_framerate,
    convert_framerate,
    get_video_duration,
    analyze_sync,
    apply_offset
)


class SyncService:
    """Service for subtitle synchronization using MLX Whisper"""

    @staticmethod
    def detect_version_info(filename: str) -> Dict[str, Any]:
        """
        Detect version/release information from filename

        Args:
            filename: Video or subtitle filename

        Returns:
            Dictionary with detected information
        """
        import re

        filename_upper = filename.upper()
        info = {
            'source': None,
            'resolution': None,
            'codec': None,
            'release_group': None,
            'year': None
        }

        # Source detection (priority order)
        sources = [
            ('BLURAY', ['BLURAY', 'BLU-RAY', 'BDRIP', 'BRRIP', 'BD']),
            ('WEB-DL', ['WEB-DL', 'WEBDL', 'WEB.DL']),
            ('WEBRip', ['WEBRIP', 'WEB-RIP', 'WEB RIP']),
            ('WEB', ['WEB']),
            ('HDTV', ['HDTV', 'HD-TV']),
            ('DVDRip', ['DVDRIP', 'DVD-RIP']),
            ('DVD', ['DVD']),
            ('HDCAM', ['HDCAM', 'HD-CAM']),
            ('CAM', ['CAM', 'CAMRIP', 'HDTS', 'TELESYNC', 'TS']),
        ]

        for source_name, patterns in sources:
            if any(pattern in filename_upper for pattern in patterns):
                info['source'] = source_name
                break

        # Resolution detection
        resolutions = ['2160P', '4K', '1080P', '720P', '576P', '480P']
        for res in resolutions:
            if res in filename_upper:
                info['resolution'] = res.replace('P', 'p')
                break

        # Codec detection
        codecs = [
            ('HEVC', ['HEVC', 'H.265', 'H265', 'X265']),
            ('H.264', ['H.264', 'H264', 'X264', 'AVC']),
            ('VP9', ['VP9']),
            ('AV1', ['AV1'])
        ]

        for codec_name, patterns in codecs:
            if any(pattern in filename_upper for pattern in patterns):
                info['codec'] = codec_name
                break

        # Year detection
        year_match = re.search(r'[.\s](\d{4})[.\s]', filename)
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2030:
                info['year'] = year

        # Release group (text after last dash)
        group_match = re.search(r'-([A-Za-z0-9]+)(?:\.\w+)?$', filename)
        if group_match:
            info['release_group'] = group_match.group(1)

        return info

    @staticmethod
    def detect_audio_language(video_path: Path, tmpdir: Path) -> str:
        """
        Detect audio language from video sample

        Args:
            video_path: Path to video file
            tmpdir: Temporary directory for audio sample

        Returns:
            Language code (en, pt, etc)
        """
        try:
            import mlx_whisper

            # Extract audio sample (1 minute starting at 60s)
            audio_sample = tmpdir / 'sample.wav'

            subprocess.run([
                'ffmpeg', '-y',
                '-ss', '60',
                '-t', '30',
                '-i', str(video_path),
                '-ac', '1',
                '-ar', '16000',
                str(audio_sample)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            # Transcribe sample to detect language
            result = mlx_whisper.transcribe(
                str(audio_sample),
                path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
            )

            language = result.get('language', 'en')
            print(f"🎙️  Detected audio language: {language}")

            return language

        except Exception as e:
            print(f"⚠️  Language detection failed: {e}")
            return 'en'  # Default to English

    @staticmethod
    def sync_subtitles(
        video_path: Path,
        subtitle_path: Path,
        output_path: Path,
        tmpdir: Path
    ) -> Dict[str, Any]:
        """
        Synchronize subtitles with video using MLX Whisper

        Args:
            video_path: Path to video file
            subtitle_path: Path to subtitle file
            output_path: Path for synchronized subtitle
            tmpdir: Temporary directory

        Returns:
            Dictionary with sync results
        """
        try:
            print(f"\n{'='*70}")
            print(f"🎬 Syncing subtitles")
            print(f"   Video: {video_path.name}")
            print(f"   Subtitle: {subtitle_path.name}")
            print(f"{'='*70}\n")

            # Step 1: Analyze framerates
            print("📊 Analyzing framerates...")
            video_fps = get_video_framerate(video_path)
            srt_fps = detect_srt_framerate(subtitle_path)

            work_file = tmpdir / 'work.srt'
            fps_diff = abs(video_fps - srt_fps) if srt_fps else 0

            # Step 2: Convert framerate if needed
            if fps_diff > 0.5:
                print(f"🔧 Converting framerate: {srt_fps} → {video_fps} fps")
                convert_framerate(subtitle_path, srt_fps, video_fps, work_file)
            else:
                import shutil
                shutil.copy(subtitle_path, work_file)

            # Step 3: Get video duration
            print("📏 Getting video duration...")
            duration = get_video_duration(video_path)
            print(f"   Duration: {duration:.1f}s")

            # Step 4: Detect audio language
            print("🎙️  Detecting audio language...")
            language = SyncService.detect_audio_language(video_path, tmpdir)

            # Step 5: Analyze sync using MLX Whisper
            print(f"\n🤖 Running MLX Whisper analysis ({language})...")
            print("   This may take 5-10 minutes...")

            offsets_list, avg_offset, std_dev = analyze_sync(
                work_file,        # srt_path
                video_path,       # video_path
                duration,         # video_duration
                num_samples=5,
                language=language
            )

            # Handle None offset
            if offsets_list is None or avg_offset is None:
                print(f"\n⚠️  Could not calculate offset")
                print(f"   Found fewer than 3 matching points")
                return {
                    'success': False,
                    'error': 'Failed to calculate synchronization offset',
                    'language': language,
                    'duration': round(duration, 1),
                    'offset_detected': None
                }

            # Calculate confidence
            if std_dev < 0.5:
                confidence = 0.95
            elif std_dev < 1.0:
                confidence = 0.80
            elif std_dev < 2.0:
                confidence = 0.60
            else:
                confidence = 0.40

            print(f"\n📊 Analysis complete:")
            print(f"   Offset: {avg_offset:+.3f}s")
            print(f"   Confidence: {confidence:.1%}")
            print(f"   Std Dev: {std_dev:.3f}s")

            # Step 6: Apply offset
            print(f"\n✏️  Applying offset of {avg_offset:+.3f}s...")
            apply_offset(work_file, avg_offset, output_path)

            print(f"\n✅ Sync complete: {output_path.name}")
            print(f"{'='*70}\n")

            details = {
                'offsets': [round(o, 3) for o in offsets_list],
                'std_dev': round(std_dev, 3),
                'num_valid_points': len(offsets_list),
                'num_total_points': 5
            }

            return {
                'success': True,
                'offset': round(avg_offset, 3),
                'confidence': round(confidence, 3),
                'video_fps': round(video_fps, 3),
                'subtitle_fps': round(srt_fps, 3) if srt_fps else None,
                'language': language,
                'duration': round(duration, 1),
                'details': details
            }

        except Exception as e:
            print(f"\n❌ Sync error: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def quick_offset(
        subtitle_path: Path,
        offset: float,
        output_path: Path
    ) -> bool:
        """
        Apply manual offset to subtitles (no ML analysis)

        Args:
            subtitle_path: Input subtitle file
            offset: Offset in seconds
            output_path: Output subtitle file

        Returns:
            True if successful
        """
        try:
            print(f"✏️  Applying manual offset: {offset:+.3f}s")
            apply_offset(subtitle_path, offset, output_path)
            print(f"✅ Offset applied: {output_path.name}")
            return True

        except Exception as e:
            print(f"❌ Offset error: {e}")
            return False

    @staticmethod
    def sync_subtitles_with_log(
        video_path: Path,
        subtitle_path: Path,
        output_path: Path,
        tmpdir: Path,
        log_path: Path,
        gcs_video_path: str = None
    ) -> Dict[str, Any]:
        """
        Synchronize subtitles with video using MLX Whisper with verbose logging

        Args:
            video_path: Path to video file (local, may be temporary)
            subtitle_path: Path to subtitle file
            output_path: Path for synchronized subtitle
            tmpdir: Temporary directory
            log_path: Path to log file for real-time progress
            gcs_video_path: Original GCS path (gs://...) or None if local upload

        Returns:
            Dictionary with sync results
        """
        def log(message: str):
            """Write message to log file and console"""
            print(message)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
                f.flush()

        try:
            log(f"{'='*70}")
            log(f"🎬 Iniciando sincronização")
            log(f"   Vídeo: {video_path.name}")
            log(f"   Legenda: {subtitle_path.name}")
            log(f"{'='*70}")
            log("")

            # Detect version information
            video_info = SyncService.detect_version_info(video_path.name)
            subtitle_info = SyncService.detect_version_info(subtitle_path.name)

            log("📋 Informação de versão detectada:")
            log("")
            log("   🎬 Vídeo:")
            if video_info['source']:
                log(f"      Fonte: {video_info['source']}")
            if video_info['resolution']:
                log(f"      Resolução: {video_info['resolution']}")
            if video_info['codec']:
                log(f"      Codec: {video_info['codec']}")
            if video_info['year']:
                log(f"      Ano: {video_info['year']}")
            if video_info['release_group']:
                log(f"      Grupo: {video_info['release_group']}")

            log("")
            log("   📄 Legendas:")
            if subtitle_info['source']:
                log(f"      Fonte: {subtitle_info['source']}")
            if subtitle_info['resolution']:
                log(f"      Resolução: {subtitle_info['resolution']}")
            if subtitle_info['year']:
                log(f"      Ano: {subtitle_info['year']}")
            if subtitle_info['release_group']:
                log(f"      Grupo: {subtitle_info['release_group']}")

            # Warn if versions don't match
            version_mismatch = False
            log("")
            if video_info['source'] and subtitle_info['source']:
                if video_info['source'] != subtitle_info['source']:
                    version_mismatch = True
                    log(f"   ⚠️  AVISO: Fontes diferentes!")
                    log(f"      Vídeo: {video_info['source']} | Legendas: {subtitle_info['source']}")
                    log(f"      Isto pode causar problemas de sincronização")

            if video_info['release_group'] and subtitle_info['release_group']:
                if video_info['release_group'] != subtitle_info['release_group']:
                    version_mismatch = True
                    log(f"   ⚠️  AVISO: Grupos de release diferentes!")
                    log(f"      Vídeo: {video_info['release_group']} | Legendas: {subtitle_info['release_group']}")

            if not version_mismatch:
                log("   ✅ Versões parecem compatíveis")

            log("")

            # Step 1: Analyze framerates
            log("📊 Analisando framerates...")
            video_fps = get_video_framerate(video_path)
            srt_fps = detect_srt_framerate(subtitle_path)

            log(f"   Vídeo: {video_fps:.3f} fps")
            if srt_fps:
                log(f"   Legenda: {srt_fps:.3f} fps")
            else:
                log(f"   Legenda: framerate não detectado")

            work_file = tmpdir / 'work.srt'
            fps_diff = abs(video_fps - srt_fps) if srt_fps else 0

            # Step 2: Convert framerate if needed
            if fps_diff > 0.5:
                log(f"🔧 Convertendo framerate: {srt_fps:.3f} → {video_fps:.3f} fps")
                convert_framerate(subtitle_path, srt_fps, video_fps, work_file)
                log("   ✅ Framerate convertido")
            else:
                log("   ✅ Framerate correto, nenhuma conversão necessária")
                import shutil
                shutil.copy(subtitle_path, work_file)

            # Step 3: Get video duration
            log("")
            log("📏 Obtendo duração do vídeo...")
            duration = get_video_duration(video_path)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            log(f"   Duração: {duration:.1f}s ({minutes}min {seconds}s)")

            # Step 4: Detect audio language
            log("")
            log("🎙️  Detectando idioma do áudio...")
            log("   Extraindo amostra de áudio (30s)...")

            import mlx_whisper
            audio_sample = tmpdir / 'sample.wav'

            subprocess.run([
                'ffmpeg', '-y',
                '-ss', '60',
                '-t', '30',
                '-i', str(video_path),
                '-ac', '1',
                '-ar', '16000',
                str(audio_sample)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            log("   Transcrevendo amostra para detectar idioma...")
            result = mlx_whisper.transcribe(
                str(audio_sample),
                path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
            )

            language = result.get('language', 'en')
            log(f"   ✅ Idioma detectado: {language.upper()}")

            # Step 5: Analyze sync using MLX Whisper
            log("")
            log(f"🤖 Iniciando análise com MLX Whisper ({language.upper()})...")
            log("   Este processo pode demorar 5-10 minutos...")
            log("")

            # Calculate sample points
            num_samples = 5
            step = duration / (num_samples + 1)
            sample_points = [step * i for i in range(1, num_samples + 1)]

            log(f"   📍 Pontos de amostragem selecionados:")
            for i, point in enumerate(sample_points, 1):
                minutes = int(point // 60)
                seconds = int(point % 60)
                log(f"      Ponto {i}: {minutes}m{seconds:02d}s")

            log("")
            log("   🎤 Extraindo e transcrevendo áudio em cada ponto...")
            log("   📝 Comparando transcrições com texto das legendas...")
            log("")

            offsets_list, avg_offset, std_dev = analyze_sync(
                work_file,
                video_path,
                duration,
                num_samples=num_samples,
                language=language,
                gcs_video_path=gcs_video_path
            )

            # Handle None (failed to find enough matches)
            if offsets_list is None or avg_offset is None:
                log("")
                log("❌ Análise falhou - Não foi possível calcular offset")
                log("")
                log("   Motivos possíveis:")
                log("   1. Foram encontrados menos de 3 pontos de correspondência")
                log("      → As legendas podem ser de uma versão diferente do vídeo")
                log("      → Exemplo: legendas de Cinema vs vídeo BluRay/WEB-DL")
                log("")
                log("   2. O idioma das legendas não corresponde ao áudio")
                log(f"      → Áudio detectado: {language.upper()}")
                log("      → Verifica se as legendas estão no mesmo idioma")
                log("")
                log("   3. Qualidade do áudio insuficiente")
                log("      → Muito ruído de fundo ou música alta")
                log("      → Compressão excessiva do áudio")
                log("")
                log("   💡 Sugestões:")
                log("      • Usa legendas da mesma fonte/release do vídeo")
                log("      • Verifica se o idioma está correto")
                log("      • Tenta com um vídeo de melhor qualidade")

                return {
                    'success': False,
                    'error': 'Não foi possível calcular o offset de sincronização',
                    'language': language,
                    'duration': round(duration, 1),
                    'offset_detected': None,
                    'video_info': video_info,
                    'subtitle_info': subtitle_info,
                    'version_mismatch': version_mismatch
                }

            # Success - show detailed results
            log("✅ Análise completa!")
            log("")
            log("   📈 Offsets detectados em cada ponto:")
            for i, off in enumerate(offsets_list, 1):
                log(f"      Ponto {i}: {off:+.3f}s")

            log("")
            log("   📊 Estatísticas:")
            log(f"      Offset médio:    {avg_offset:+.3f}s")
            log(f"      Desvio padrão:   {std_dev:.3f}s")

            # Calculate confidence based on standard deviation
            # Lower std_dev = higher confidence
            if std_dev < 0.5:
                confidence = 0.95
                confidence_text = "ALTA"
            elif std_dev < 1.0:
                confidence = 0.80
                confidence_text = "MÉDIA-ALTA"
            elif std_dev < 2.0:
                confidence = 0.60
                confidence_text = "MÉDIA"
            else:
                confidence = 0.40
                confidence_text = "BAIXA"

            log(f"      Confiança:       {confidence:.1%} ({confidence_text})")
            log(f"      Pontos válidos:  {len(offsets_list)}/{num_samples}")

            if std_dev > 1.0:
                log("")
                log(f"   ⚠️  Desvio padrão elevado ({std_dev:.3f}s)")
                log("      Pode haver inconsistências na sincronização")
                log("      Verifica se as legendas correspondem ao vídeo")

            # Step 6: Apply offset
            log("")
            log(f"✏️  Aplicando correção de {avg_offset:+.3f}s às legendas...")
            apply_offset(work_file, avg_offset, output_path)

            log("")
            log(f"✅ Sincronização concluída: {output_path.name}")
            log(f"{'='*70}")
            log("Complete")  # Signal completion

            # Build details dictionary
            details = {
                'offsets': [round(o, 3) for o in offsets_list],
                'std_dev': round(std_dev, 3),
                'num_valid_points': len(offsets_list),
                'num_total_points': num_samples,
                'confidence_level': confidence_text
            }

            return {
                'success': True,
                'offset_detected': round(avg_offset, 3),
                'confidence': round(confidence, 3),
                'video_fps': round(video_fps, 3),
                'subtitle_fps': round(srt_fps, 3) if srt_fps else None,
                'language': language,
                'duration': round(duration, 1),
                'details': details,
                'video_info': video_info,
                'subtitle_info': subtitle_info,
                'version_mismatch': version_mismatch
            }

        except Exception as e:
            log("")
            log(f"❌ Erro na sincronização: {e}")
            import traceback
            log(traceback.format_exc())
            log("Complete")  # Signal completion even on error

            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_sync_stats(details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get human-readable sync statistics

        Args:
            details: Sync details from analyze_sync

        Returns:
            Formatted statistics
        """
        if not details:
            return {}

        return {
            'total_matches': details.get('total_matches', 0),
            'avg_correlation': round(details.get('avg_correlation', 0), 3),
            'confidence_level': 'high' if details.get('avg_correlation', 0) > 0.7 else 'medium' if details.get('avg_correlation', 0) > 0.5 else 'low',
            'processing_time': f"{details.get('processing_time', 0):.1f}s" if 'processing_time' in details else 'N/A'
        }
