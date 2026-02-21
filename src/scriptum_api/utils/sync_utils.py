#!/usr/bin/env python3
"""
Scriptum v2.2 - Sincronização Inteligente com Conversão de Framerate
Detecta problemas de framerate E sincronização, corrige automaticamente

Uso: python3 smart_sync.py <video> <legenda.srt>
"""

import subprocess
import tempfile
from pathlib import Path
import sys
import pysrt
import statistics
import re


def get_video_framerate(video_path):
    """Obtém framerate do vídeo"""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
        text=True
    )
    frac = result.stdout.strip()
    num, den = map(int, frac.split('/'))
    return round(num / den, 3)


def detect_srt_framerate(srt_path):
    """Infere framerate das legendas SRT"""
    subs = pysrt.open(srt_path)

    if len(subs) < 100:
        return None

    # Analisar padrão de milissegundos
    ms_values = []
    for sub in subs[:200]:
        ms = sub.start.milliseconds
        ms_values.append(ms)

    # Framerates comuns e seus padrões
    common_fps = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
    frame_durations = {fps: 1000 / fps for fps in common_fps}

    # Contar múltiplos de cada frame duration
    best_fps = 25.0
    best_score = 0

    for fps, frame_ms in frame_durations.items():
        score = sum(1 for ms in ms_values if abs(ms % frame_ms) < 5)
        if score > best_score:
            best_score = score
            best_fps = fps

    return best_fps


def convert_framerate(srt_path, from_fps, to_fps, output_path):
    """Converte framerate das legendas"""
    subs = pysrt.open(srt_path)
    ratio = to_fps / from_fps

    for sub in subs:
        # Converter timestamps
        start_ms = sub.start.ordinal
        end_ms = sub.end.ordinal

        sub.start.ordinal = int(start_ms * ratio)
        sub.end.ordinal = int(end_ms * ratio)

    subs.save(output_path)


def get_video_duration(video_path):
    """Obtém duração do vídeo"""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
        text=True
    )
    return float(result.stdout.strip())


def get_audio_codec(video_path):
    """Deteta o codec de áudio do vídeo"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        codec = result.stdout.strip().lower()
        return codec
    except:
        return None


def ensure_compatible_audio_cached(video_path):
    """
    Garante que existe uma versão AAC do áudio e retorna o caminho.

    Se o vídeo tem áudio AC3/DTS/etc:
    - Verifica se já existe ficheiro .aac na mesma pasta
    - Se não existir, converte e guarda
    - Retorna caminho do .aac para uso em extrações

    Args:
        video_path: Caminho do vídeo original

    Returns:
        Caminho do ficheiro AAC (ou vídeo original se já for compatível)
    """
    video_path = Path(video_path)

    # Verificar codec de áudio
    codec = get_audio_codec(video_path)

    # Codecs incompatíveis que precisam conversão
    incompatible_codecs = ['ac3', 'dts', 'eac3', 'truehd', 'dts-hd']

    # Se codec é compatível (aac, mp3, opus, etc), usa vídeo original
    if codec not in incompatible_codecs:
        print(f"   ✅ Áudio já compatível ({codec.upper() if codec else 'unknown'})")
        return video_path

    # Caminho do AAC cache (mesma pasta, mesmo nome, extensão .aac)
    aac_cache_path = video_path.with_suffix('.aac')

    # Se cache já existe, reutiliza
    if aac_cache_path.exists():
        cache_size_mb = aac_cache_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ Usando áudio AAC em cache ({cache_size_mb:.1f}MB)")
        print(f"      {aac_cache_path.name}")
        return aac_cache_path

    # Converter áudio completo para AAC
    print(f"   🔄 Convertendo áudio {codec.upper()} → AAC...")
    print(f"      Isto só acontece uma vez, será guardado para uso futuro")

    try:
        # Extrair todo o áudio e converter para AAC
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-vn",  # Sem vídeo
                "-c:a", "aac",
                "-b:a", "192k",  # Qualidade boa
                str(aac_cache_path)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        cache_size_mb = aac_cache_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ AAC criado e guardado ({cache_size_mb:.1f}MB)")
        print(f"      {aac_cache_path.name}")
        print(f"      Próximas sincronizações serão mais rápidas!")

        return aac_cache_path

    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Conversão falhou, usando vídeo original")
        return video_path


def extract_audio(video_path, audio_path, start_time=0, duration=60):
    """
    Extrai segmento de áudio do vídeo.
    Se o vídeo tem áudio AC3/DTS, usa cache AAC automaticamente.
    """
    # Garantir que temos áudio compatível (usa cache se disponível)
    audio_source = ensure_compatible_audio_cached(video_path)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", str(audio_source),  # Usa AAC cache se disponível
            "-ac", "1",
            "-ar", "16000",
            str(audio_path)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )


def transcribe(audio_path, language="en"):
    """Transcreve áudio com Whisper MLX"""
    import mlx_whisper
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo="mlx-community/whisper-tiny",
        language=language  # Forçar inglês para máxima precisão!
    )
    return result["segments"]


def compute_offset_for_segment(srt_path, segments, start_time_offset):
    """Calcula offset para um segmento"""
    subs = pysrt.open(srt_path)
    offsets = []

    for seg in segments[:15]:
        absolute_time = start_time_offset + seg["start"]

        for sub in subs:
            sub_time = sub.start.ordinal / 1000
            if abs(sub_time - absolute_time) < 5:
                offsets.append(absolute_time - sub_time)
                break

    if not offsets:
        return None

    return statistics.median(offsets)


def analyze_sync(srt_path, video_path, video_duration, num_samples=5, language="en"):
    """Analisa sincronização"""
    sample_points = []
    step = video_duration / (num_samples + 1)
    for i in range(1, num_samples + 1):
        sample_points.append(step * i)

    offsets = []

    with tempfile.TemporaryDirectory() as tmp:
        for idx, start_time in enumerate(sample_points, 1):
            audio = Path(tmp) / f"sample_{idx}.wav"
            extract_audio(video_path, audio, start_time=int(start_time), duration=45)
            segments = transcribe(audio, language=language)
            offset = compute_offset_for_segment(srt_path, segments, start_time)
            if offset is not None:
                offsets.append(offset)

    if len(offsets) < 3:
        return None, None, None

    avg_offset = statistics.mean(offsets)
    std_dev = statistics.stdev(offsets) if len(offsets) > 1 else 0

    return offsets, avg_offset, std_dev


def apply_offset(srt_path, offset_seconds, output_path):
    """Aplica offset"""
    subs = pysrt.open(srt_path)
    subs.shift(seconds=offset_seconds)
    subs.save(output_path)


def main(video_path, srt_path):
    video = Path(video_path)
    srt_original = Path(srt_path)

    print("\n🎬 Scriptum v2.2 - Sincronização Inteligente")
    print("=" * 70)
    print(f"📹 Vídeo:   {video.name}")
    print(f"📄 Legenda: {srt_original.name}")
    print("=" * 70)

    # Obter framerates
    print("\n📊 A analisar framerates...")
    video_fps = get_video_framerate(video)
    srt_fps = detect_srt_framerate(srt_original)

    print(f"   🎞️  Vídeo:    {video_fps} fps")
    print(f"   📄  Legenda:  {srt_fps} fps")

    work_file = srt_original.with_suffix('.work.srt')

    # Verificar se precisa conversão de framerate
    fps_diff = abs(video_fps - srt_fps) if srt_fps else 0

    if fps_diff > 0.5:
        print(f"\n⚠️  INCOMPATIBILIDADE DE FRAMERATE DETECTADA!")
        print(f"   Diferença: {fps_diff:.2f} fps")
        print(f"\n🔧 A converter legendas: {srt_fps} fps → {video_fps} fps...")

        convert_framerate(srt_original, srt_fps, video_fps, work_file)
        print(f"   ✅ Conversão concluída!")
    else:
        print(f"   ✅ Framerates compatíveis")
        import shutil
        shutil.copy(srt_original, work_file)

    # Obter duração
    duration = get_video_duration(video)
    print(f"\n📏 Duração: {int(duration//60)}min {int(duration%60)}s")

    # Detectar idioma do áudio
    print(f"\n🎙️  A detectar idioma do áudio...")
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "sample.wav"
        extract_audio(video, audio, start_time=60, duration=30)
        result = mlx_whisper.transcribe(str(audio), path_or_hf_repo="mlx-community/whisper-tiny")
        detected_lang = result.get("language", "en")

    print(f"   ✅ Idioma detectado: {detected_lang.upper()}")

    # Análise de sincronização
    print(f"\n🔍 A analisar sincronização em 5 pontos...")
    offsets, avg_offset, std_dev = analyze_sync(
        work_file, video, duration, num_samples=5, language=detected_lang
    )

    if offsets is None:
        print("❌ Erro na análise")
        work_file.unlink()
        sys.exit(1)

    print(f"\n   📈 Offsets detectados:")
    for i, off in enumerate(offsets, 1):
        print(f"      Ponto {i}: {off:+.2f}s")

    print(f"\n   📊 Estatísticas:")
    print(f"      Média:          {avg_offset:+.2f}s")
    print(f"      Desvio padrão:  {std_dev:.2f}s")

    # Aplicar correção se necessário
    if abs(avg_offset) > 0.2:
        print(f"\n🔧 A aplicar correção de sincronização: {avg_offset:+.2f}s")
        apply_offset(work_file, avg_offset, work_file)
        print(f"   ✅ Correção aplicada!")
    else:
        print(f"\n   ✅ Já está sincronizado ({avg_offset:+.2f}s)")

    # Guardar resultado
    output = srt_original.with_name(srt_original.stem + ".sync.srt")
    import shutil
    shutil.move(work_file, output)

    print(f"\n{'='*70}")
    print(f"✅ SINCRONIZAÇÃO CONCLUÍDA!")
    print(f"{'='*70}")

    if fps_diff > 0.5:
        print(f"\n📊 Correções aplicadas:")
        print(f"   • Framerate: {srt_fps} → {video_fps} fps")
        print(f"   • Offset:    {avg_offset:+.2f}s")
    else:
        print(f"\n📊 Correção aplicada:")
        print(f"   • Offset:    {avg_offset:+.2f}s")

    print(f"\n📁 Ficheiro criado:")
    print(f"   {output}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("=" * 70)
        print("🎬 Scriptum v2.2 - Sincronização Inteligente")
        print("=" * 70)
        print("\nUso: python3 smart_sync.py <video> <legenda.srt>")
        print("\nO que faz:")
        print("  • Detecta framerate do vídeo e legendas")
        print("  • Converte framerate se necessário")
        print("  • Detecta idioma automaticamente")
        print("  • Sincroniza com Whisper (precisão máxima)")
        print("=" * 70)
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
