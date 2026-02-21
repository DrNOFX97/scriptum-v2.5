#!/usr/bin/env python3
"""
Detector de Framerate de Legendas e Vídeos MKV
"""

import subprocess
import json
import re
import sys
from collections import Counter

def get_mkv_framerate(mkv_path):
    """Obtém o framerate do vídeo MKV usando mkvmerge"""
    try:
        result = subprocess.run(
            ['mkvmerge', '-J', mkv_path],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        # Procurar tracks de vídeo
        for track in data.get('tracks', []):
            if track.get('type') == 'video':
                props = track.get('properties', {})

                # Framerate pode estar em diferentes formatos
                if 'default_duration' in props:
                    # default_duration está em nanosegundos por frame
                    ns_per_frame = props['default_duration']
                    fps = 1_000_000_000 / ns_per_frame
                    return round(fps, 3)

                # Alguns MKVs têm display_dimensions ou pixel_dimensions
                # mas não sempre têm framerate explícito

        return None

    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return None

def detect_srt_framerate(srt_path):
    """
    Tenta inferir o framerate analisando os timestamps das legendas.
    Legendas geralmente usam timestamps com precisão de milissegundos,
    mas o padrão de repetição pode indicar o framerate original.
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extrair todos os timestamps
        timestamp_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})'
        matches = re.findall(timestamp_pattern, content)

        if not matches:
            return None

        # Converter para milissegundos
        milliseconds = []
        for h, m, s, ms in matches:
            total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
            milliseconds.append(total_ms)

        # Calcular diferenças entre timestamps consecutivos
        diffs = []
        for i in range(1, len(milliseconds)):
            diff = milliseconds[i] - milliseconds[i-1]
            if diff > 0:  # Ignorar timestamps iguais
                diffs.append(diff)

        if not diffs:
            return None

        # Analisar os intervalos mais comuns
        # Um framerate comum terá múltiplos de 1/fps segundos
        common_framerates = {
            23.976: 1000 / 23.976,  # ~41.71 ms
            24.000: 1000 / 24.000,  # 41.67 ms
            25.000: 1000 / 25.000,  # 40.00 ms
            29.970: 1000 / 29.970,  # ~33.37 ms
            30.000: 1000 / 30.000,  # 33.33 ms
            50.000: 1000 / 50.000,  # 20.00 ms
            59.940: 1000 / 59.940,  # ~16.68 ms
            60.000: 1000 / 60.000,  # 16.67 ms
        }

        # Verificar qual framerate se encaixa melhor
        best_match = None
        best_score = 0

        for fps, frame_ms in common_framerates.items():
            # Contar quantos timestamps são múltiplos próximos deste framerate
            matches = 0
            for diff in diffs:
                # Verificar se diff é próximo de um múltiplo de frame_ms
                frames = diff / frame_ms
                nearest_int = round(frames)
                error = abs(frames - nearest_int)

                if error < 0.1:  # Tolerância de 10%
                    matches += 1

            score = matches / len(diffs)
            if score > best_score:
                best_score = score
                best_match = fps

        # Só retornar se tiver pelo menos 30% de confiança
        if best_score > 0.3:
            return best_match

        return None

    except Exception as e:
        print(f"Erro ao analisar SRT: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 detect_framerate.py <ficheiro.mkv|ficheiro.srt>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"🎬 Analisando: {filepath}")
    print("=" * 60)

    if filepath.endswith('.mkv'):
        fps = get_mkv_framerate(filepath)
        if fps:
            print(f"✅ Framerate do vídeo MKV: {fps} fps")

            # Sugerir o framerate comum mais próximo
            common_fps = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
            closest = min(common_fps, key=lambda x: abs(x - fps))
            if abs(closest - fps) < 0.1:
                print(f"   (Padrão comum: {closest} fps)")
        else:
            print("⚠️  Não foi possível detectar o framerate do MKV")

    elif filepath.endswith('.srt'):
        fps = detect_srt_framerate(filepath)
        if fps:
            print(f"✅ Framerate inferido das legendas: {fps} fps")
            print(f"   (Baseado na análise dos timestamps)")
        else:
            print("⚠️  Não foi possível inferir o framerate das legendas")
            print("   As legendas podem não ter padrão de framerate consistente")

    else:
        print("❌ Formato não suportado. Use .mkv ou .srt")
        sys.exit(1)

    print("=" * 60)

if __name__ == '__main__':
    main()
