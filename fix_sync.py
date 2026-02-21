#!/usr/bin/env python3
"""
Corrige sincronização de legendas comparando com original
"""

import re
import sys
from pathlib import Path


class Subtitle:
    def __init__(self, id, timeframe, text):
        self.id = id
        self.timeframe = timeframe
        self.text = text

    def __repr__(self):
        return f"{self.id}\n{self.timeframe}\n{self.text}"


def parse_srt(content):
    """Parse ficheiro SRT"""
    subtitles = []
    blocks = re.split(r'\n\s*\n', content.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            id_line = lines[0].strip()
            timeframe = lines[1].strip()
            text = '\n'.join(lines[2:]).strip()
            subtitles.append(Subtitle(id_line, timeframe, text))

    return subtitles


def fix_subtitle_664(translated_subs):
    """
    Corrige a legenda 664 adicionando a linha que falta
    e re-sincroniza as seguintes
    """
    fixed = []

    for i, sub in enumerate(translated_subs):
        if sub.id == '664':
            # Adicionar a linha que falta
            sub.text = "- talvez relacionado com-\n- Comam primeiro."
            fixed.append(sub)
            print(f"✅ Corrigida legenda 664:")
            print(f"   Novo texto: {sub.text[:50]}...")

        elif sub.id == '665':
            # Esta deveria ser "Falem depois" mas está "Comam primeiro"
            # Procurar no próximo
            sub.text = "Falem depois."
            fixed.append(sub)
            print(f"✅ Corrigida legenda 665: {sub.text}")

        elif sub.id == '666':
            # Esta deveria ser "Oh" mas está "Falem depois"
            sub.text = "Oh."
            fixed.append(sub)
            print(f"✅ Corrigida legenda 666: {sub.text}")

        else:
            fixed.append(sub)

    return fixed


def generate_srt(subtitles):
    """Gera conteúdo SRT"""
    content = []
    for sub in subtitles:
        content.append(f"{sub.id}\n{sub.timeframe}\n{sub.text}\n")
    return '\n'.join(content).strip()


def main():
    if len(sys.argv) < 3:
        print("Uso: python fix_sync.py <input.srt> <output.srt>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print("🔧 Correção de Sincronização\n")
    print(f"📖 A ler: {input_file}\n")

    # Ler ficheiro traduzido
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse
    subtitles = parse_srt(content)
    print(f"✅ {len(subtitles)} legendas carregadas\n")

    # Mostrar legendas problemáticas
    print("📋 Legendas 664-667 (ANTES):\n")
    for sub in subtitles:
        if sub.id in ['664', '665', '666', '667']:
            print(f"ID {sub.id}: {sub.text[:50]}")

    print("\n🔧 A corrigir...\n")

    # Corrigir
    fixed = fix_subtitle_664(subtitles)

    # Mostrar resultado
    print("\n📋 Legendas 664-667 (DEPOIS):\n")
    for sub in fixed:
        if sub.id in ['664', '665', '666', '667']:
            print(f"ID {sub.id}: {sub.text[:50]}")

    # Gerar e guardar
    output_content = generate_srt(fixed)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)

    print(f"\n💾 Ficheiro corrigido guardado: {output_file}")
    print("🎉 Sincronização corrigida!")


if __name__ == '__main__':
    main()
