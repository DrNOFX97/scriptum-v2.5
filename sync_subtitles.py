#!/usr/bin/env python3
"""
Scriptum v2.0 - Sincronização Automática de Legendas
Usa Whisper MLX (otimizado para Apple Silicon) para detectar e corrigir delays

Uso: python3 sync_subtitles.py <video> <legenda.srt>
"""

import subprocess
import tempfile
from pathlib import Path
import sys
import pysrt
import mlx_whisper


def get_video_duration(video_path):
    """Obtém a duração total do vídeo em segundos"""
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


def extract_audio(video_path, audio_path, start_time=0, duration=60):
    """Extrai segmento de áudio do vídeo"""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", str(video_path),
            "-ac", "1",
            "-ar", "16000",
            str(audio_path)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )


def transcribe(audio_path):
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo="mlx-community/whisper-tiny",
        language=None
    )
    return result["segments"]


def compute_offset_for_segment(srt_path, segments, start_time_offset):
    """Calcula offset para um segmento específico do vídeo"""
    subs = pysrt.open(srt_path)
    offsets = []

    for seg in segments[:20]:  # Máximo 20 amostras por segmento
        # Tempo absoluto do segmento no vídeo
        absolute_time = start_time_offset + seg["start"]

        # Procurar legenda correspondente
        for sub in subs:
            sub_time = sub.start.ordinal / 1000
            # Se a legenda está próxima do tempo do segmento (±5s)
            if abs(sub_time - absolute_time) < 5:
                offsets.append(absolute_time - sub_time)
                break

    if not offsets:
        return None

    return sum(offsets) / len(offsets)


def apply_offset(srt_path, offset_seconds, output_path):
    subs = pysrt.open(srt_path)
    subs.shift(seconds=offset_seconds)
    subs.save(output_path)


def run_ffsubsync(video_path, srt_path, output_path):
    subprocess.run(
        [
            "ffsubsync",
            str(video_path),
            "-i", str(srt_path),
            "-o", str(output_path)
        ],
        check=True
    )


def main(video_path, srt_path):
    video = Path(video_path)
    srt = Path(srt_path)

    print("\n🎬 Scriptum v2.0 - Sincronização Automática Avançada")
    print("=" * 60)
    print(f"📹 Vídeo:   {video.name}")
    print(f"📄 Legenda: {srt.name}")
    print("=" * 60)

    # Obter duração do vídeo
    print("\n📏 A analisar vídeo...")
    duration = get_video_duration(video)
    print(f"   ✅ Duração: {int(duration//60)}min {int(duration%60)}s")

    # Definir pontos de análise: início, meio e fim
    sample_points = [
        (60, "início"),           # 1 minuto
        (duration / 2, "meio"),   # Meio do filme
        (duration - 180, "fim")   # 3 min antes do fim
    ]

    with tempfile.TemporaryDirectory() as tmp:
        offsets = []

        print(f"\n🎙️  A analisar {len(sample_points)} pontos do filme...")

        for i, (start_time, label) in enumerate(sample_points, 1):
            if start_time < 0:
                continue

            audio = Path(tmp) / f"audio_{label}.wav"

            print(f"\n   [{i}/{len(sample_points)}] {label.capitalize()} ({int(start_time//60)}min)...")

            # Extrair 60 segundos de áudio
            extract_audio(video, audio, start_time=int(start_time), duration=60)

            # Transcrever
            segments = transcribe(audio)
            print(f"       ✅ {len(segments)} segmentos transcritos")

            # Calcular offset
            offset = compute_offset_for_segment(srt, segments, start_time)
            if offset is not None:
                offsets.append(offset)
                print(f"       📊 Offset: {offset:+.2f}s")

        if not offsets:
            print("\n❌ Não foi possível calcular sincronização")
            sys.exit(1)

        # Calcular média dos offsets
        avg_offset = sum(offsets) / len(offsets)

        print(f"\n⏱️  Desvio médio calculado: {avg_offset:+.2f} segundos")
        print(f"   📊 Baseado em {len(offsets)} amostras")

        if avg_offset > 0:
            print("   📌 Legendas estão ATRASADAS")
        elif avg_offset < 0:
            print("   📌 Legendas estão ADIANTADAS")
        else:
            print("   📌 Legendas estão PERFEITAS!")

        output = srt.with_name(srt.stem + ".sync.srt")

        print("\n🔧 A aplicar correção...")
        print(f"   Método: Offset automático ({avg_offset:+.2f}s)")
        apply_offset(srt, avg_offset, output)

        print("\n" + "=" * 60)
        print(f"✅ Legenda sincronizada criada:")
        print(f"   {output}")
        print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("=" * 60)
        print("🎬 Scriptum v2.0 - Sincronização Automática de Legendas")
        print("=" * 60)
        print("\nUso: python3 sync_subtitles.py <video> <legenda.srt>")
        print("\nExemplo:")
        print('  python3 sync_subtitles.py "filme.mkv" "legendas.srt"')
        print("\nO que faz:")
        print("  • Extrai áudio do vídeo (primeiros 2 minutos)")
        print("  • Transcreve com Whisper MLX (Apple Silicon)")
        print("  • Calcula offset entre legenda e vídeo")
        print("  • Corrige automaticamente o delay")
        print("\nRequisitos:")
        print("  pip install pysrt mlx-whisper ffsubsync")
        print("  brew install ffmpeg")
        print("=" * 60)
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
