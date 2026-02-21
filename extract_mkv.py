#!/usr/bin/env python3
"""
Script simples para extrair legendas de ficheiros MKV
Uso: python3 extract_mkv.py <caminho_do_mkv>
"""

import sys
import os
import subprocess
import json
import re
from mkv.subtitle_extractor import MKVSubtitleExtractor

def get_mkv_framerate(mkv_path):
    """Obtém o framerate do vídeo MKV"""
    try:
        result = subprocess.run(
            ['mkvmerge', '-J', mkv_path],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        for track in data.get('tracks', []):
            if track.get('type') == 'video':
                props = track.get('properties', {})
                if 'default_duration' in props:
                    ns_per_frame = props['default_duration']
                    fps = 1_000_000_000 / ns_per_frame
                    return round(fps, 3)
        return None
    except:
        return None

def detect_srt_framerate(srt_path):
    """Infere o framerate das legendas SRT"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        timestamp_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})'
        matches = re.findall(timestamp_pattern, content)

        if not matches:
            return None

        milliseconds = []
        for h, m, s, ms in matches:
            total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
            milliseconds.append(total_ms)

        diffs = [milliseconds[i] - milliseconds[i-1] for i in range(1, len(milliseconds)) if milliseconds[i] - milliseconds[i-1] > 0]

        if not diffs:
            return None

        common_framerates = {
            23.976: 1000 / 23.976,
            24.000: 1000 / 24.000,
            25.000: 1000 / 25.000,
            29.970: 1000 / 29.970,
            30.000: 1000 / 30.000,
            50.000: 1000 / 50.000,
            59.940: 1000 / 59.940,
            60.000: 1000 / 60.000,
        }

        best_match = None
        best_score = 0

        for fps, frame_ms in common_framerates.items():
            matches = 0
            for diff in diffs:
                frames = diff / frame_ms
                nearest_int = round(frames)
                error = abs(frames - nearest_int)
                if error < 0.1:
                    matches += 1

            score = matches / len(diffs)
            if score > best_score:
                best_score = score
                best_match = fps

        if best_score > 0.3:
            return best_match

        return None
    except:
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_mkv.py <caminho_do_mkv>")
        print("\nExemplo:")
        print("  python3 extract_mkv.py '/Users/f.nuno/Downloads/filme.mkv'")
        sys.exit(1)

    mkv_path = sys.argv[1]

    # Verificar se ficheiro existe
    if not os.path.exists(mkv_path):
        print(f"❌ Erro: Ficheiro não encontrado: {mkv_path}")
        sys.exit(1)

    print(f"🎬 Analisando: {os.path.basename(mkv_path)}")
    print("=" * 60)

    # Detectar framerate do vídeo
    fps = get_mkv_framerate(mkv_path)
    if fps:
        print(f"🎞️  Framerate do vídeo: {fps} fps")
    else:
        print("⚠️  Framerate não detectado")
    print()

    # Inicializar extractor
    extractor = MKVSubtitleExtractor()

    # Listar tracks de legendas
    try:
        tracks = extractor.list_subtitle_tracks(mkv_path)

        if not tracks:
            print("ℹ️  Nenhuma legenda encontrada neste ficheiro MKV")
            sys.exit(0)

        print(f"\n📋 Encontradas {len(tracks)} track(s) de legendas:\n")

        for i, track in enumerate(tracks, 1):
            default_marker = " [PADRÃO]" if track.is_default else ""
            print(f"{i}. Track {track.track_id}: {track.language} - {track.codec}{default_marker}")
            if track.track_name:
                print(f"   Nome: {track.track_name}")
            print()

        # Perguntar quais extrair
        print("=" * 60)
        response = input("Extrair todas as legendas? (s/n): ").strip().lower()

        if response == 's':
            track_ids = [track.track_id for track in tracks]
        else:
            track_input = input("Digite os números das tracks separados por vírgula (ex: 1,3): ").strip()
            try:
                indices = [int(x.strip()) for x in track_input.split(',')]
                track_ids = [tracks[i-1].track_id for i in indices if 1 <= i <= len(tracks)]
            except (ValueError, IndexError):
                print("❌ Entrada inválida!")
                sys.exit(1)

        if not track_ids:
            print("ℹ️  Nenhuma track selecionada")
            sys.exit(0)

        # Diretório de saída (mesma pasta do MKV)
        output_dir = os.path.dirname(mkv_path) or '.'

        print(f"\n🚀 Extraindo {len(track_ids)} legenda(s)...")
        print(f"📁 Pasta de saída: {output_dir}\n")

        # Extrair
        extracted = extractor.extract_multiple(mkv_path, track_ids, output_dir)

        print("\n✅ Extração concluída!\n")
        print("📄 Ficheiros criados:")
        for filepath in extracted:
            file_size = os.path.getsize(filepath)
            size_kb = file_size / 1024
            print(f"  • {os.path.basename(filepath)} ({size_kb:.1f} KB)")

            # Detectar framerate da legenda
            srt_fps = detect_srt_framerate(filepath)
            if srt_fps:
                print(f"    🎞️  Framerate: {srt_fps} fps")

        print("\n" + "=" * 60)
        print("✨ Pode agora traduzir estes ficheiros SRT na interface web")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
