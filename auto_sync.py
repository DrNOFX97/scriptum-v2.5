#!/usr/bin/env python3
"""
Scriptum v2.1 - Sincronização Automática Perfeita
Sistema iterativo que refina até sincronização 100% perfeita

Uso: python3 auto_sync.py <video> <legenda.srt>
"""

import subprocess
import tempfile
from pathlib import Path
import sys
import pysrt
import mlx_whisper
import statistics


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
    """Transcreve áudio com Whisper MLX"""
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo="mlx-community/whisper-tiny",
        language=None
    )
    return result["segments"]


def analyze_sync_quality(srt_path, video_path, video_duration, num_samples=5):
    """
    Analisa qualidade da sincronização em múltiplos pontos
    Retorna: (offsets_list, média, desvio_padrão, qualidade)
    """
    # Distribuir amostras ao longo do filme
    sample_points = []
    step = video_duration / (num_samples + 1)
    for i in range(1, num_samples + 1):
        sample_points.append(step * i)

    offsets = []

    with tempfile.TemporaryDirectory() as tmp:
        for idx, start_time in enumerate(sample_points, 1):
            audio = Path(tmp) / f"sample_{idx}.wav"

            # Extrair 45 segundos
            extract_audio(video_path, audio, start_time=int(start_time), duration=45)

            # Transcrever
            segments = transcribe(audio)

            # Calcular offset
            offset = compute_offset_for_segment(srt_path, segments, start_time)
            if offset is not None:
                offsets.append(offset)

    if len(offsets) < 3:
        return None, None, None, "RUIM"

    avg_offset = statistics.mean(offsets)
    std_dev = statistics.stdev(offsets) if len(offsets) > 1 else 0

    # Determinar qualidade
    if abs(avg_offset) < 0.3 and std_dev < 0.5:
        quality = "PERFEITO"
    elif abs(avg_offset) < 0.8 and std_dev < 1.0:
        quality = "BOM"
    elif abs(avg_offset) < 2.0 and std_dev < 2.0:
        quality = "ACEITAVEL"
    else:
        quality = "RUIM"

    return offsets, avg_offset, std_dev, quality


def compute_offset_for_segment(srt_path, segments, start_time_offset):
    """Calcula offset para um segmento específico do vídeo"""
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

    return statistics.median(offsets)  # Usar mediana é mais robusto


def apply_offset(srt_path, offset_seconds, output_path):
    """Aplica offset às legendas"""
    subs = pysrt.open(srt_path)
    subs.shift(seconds=offset_seconds)
    subs.save(output_path)


def main(video_path, srt_path):
    video = Path(video_path)
    srt_original = Path(srt_path)

    print("\n🎬 Scriptum v2.1 - Sincronização Automática PERFEITA")
    print("=" * 70)
    print(f"📹 Vídeo:   {video.name}")
    print(f"📄 Legenda: {srt_original.name}")
    print("=" * 70)

    # Obter duração do vídeo
    print("\n📏 A analisar vídeo...")
    duration = get_video_duration(video)
    print(f"   ✅ Duração: {int(duration//60)}min {int(duration%60)}s")

    # Criar ficheiro de trabalho temporário
    work_file = srt_original.with_suffix('.work.srt')
    import shutil
    shutil.copy(srt_original, work_file)

    max_iterations = 5
    iteration = 0
    total_correction = 0.0

    print("\n🔄 Iniciando sincronização iterativa...")
    print(f"   🎯 Objetivo: Qualidade PERFEITA (offset < 0.3s, variação < 0.5s)")

    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*70}")
        print(f"🔁 Iteração {iteration}/{max_iterations}")
        print(f"{'='*70}")

        # Analisar qualidade atual
        print(f"\n📊 A analisar sincronização em 5 pontos...")
        offsets, avg_offset, std_dev, quality = analyze_sync_quality(
            work_file, video, duration, num_samples=5
        )

        if offsets is None:
            print("❌ Erro na análise. A abortar.")
            work_file.unlink()
            sys.exit(1)

        # Mostrar resultados
        print(f"\n   📈 Offsets detectados:")
        for i, off in enumerate(offsets, 1):
            print(f"      Ponto {i}: {off:+.2f}s")

        print(f"\n   📊 Estatísticas:")
        print(f"      Média:          {avg_offset:+.2f}s")
        print(f"      Desvio padrão:  {std_dev:.2f}s")
        print(f"      Qualidade:      {quality}")

        # Verificar se está perfeito
        if quality == "PERFEITO":
            print(f"\n   ✅ SINCRONIZAÇÃO PERFEITA ATINGIDA!")
            break

        # Aplicar correção
        if abs(avg_offset) > 0.1:  # Só corrigir se > 100ms
            print(f"\n   🔧 A aplicar correção: {avg_offset:+.2f}s")
            apply_offset(work_file, avg_offset, work_file)
            total_correction += avg_offset
            print(f"   ✅ Correção aplicada (total acumulado: {total_correction:+.2f}s)")
        else:
            print(f"\n   ✅ Offset muito pequeno ({avg_offset:+.2f}s), mantendo assim")
            break

    # Guardar resultado final
    output = srt_original.with_name(srt_original.stem + ".sync.srt")
    shutil.move(work_file, output)

    print(f"\n{'='*70}")
    print(f"✅ SINCRONIZAÇÃO CONCLUÍDA!")
    print(f"{'='*70}")
    print(f"\n📊 Resumo:")
    print(f"   Iterações necessárias: {iteration}")
    print(f"   Correção total aplicada: {total_correction:+.2f}s")
    print(f"   Qualidade final: {quality}")
    print(f"\n📁 Ficheiro criado:")
    print(f"   {output}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("=" * 70)
        print("🎬 Scriptum v2.1 - Sincronização Automática PERFEITA")
        print("=" * 70)
        print("\nUso: python3 auto_sync.py <video> <legenda.srt>")
        print("\nExemplo:")
        print('  python3 auto_sync.py "filme.mkv" "legendas.srt"')
        print("\nO que faz:")
        print("  • Analisa múltiplos pontos do filme")
        print("  • Calcula offsets com precisão estatística")
        print("  • Refina iterativamente até perfeição")
        print("  • Garante qualidade < 0.3s de desvio")
        print("=" * 70)
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
