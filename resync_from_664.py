#!/usr/bin/env python3
"""
Re-sincroniza legendas a partir da 664, corrigindo o deslocamento
"""

import re
from pathlib import Path


class Subtitle:
    def __init__(self, id, timeframe, text):
        self.id = id
        self.timeframe = timeframe
        self.text = text


def parse_srt(content):
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


def generate_srt(subtitles):
    content = []
    for sub in subtitles:
        content.append(f"{sub.id}\n{sub.timeframe}\n{sub.text}\n")
    return '\n'.join(content).strip()


# Ler ficheiro original (inglês)
print("📖 A ler ficheiros...\n")

with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt', 'r', encoding='utf-8') as f:
    original_content = f.read()

with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FIXED.srt', 'r', encoding='utf-8') as f:
    translated_content = f.read()

original_subs = parse_srt(original_content)
translated_subs = parse_srt(translated_content)

print(f"✅ Original: {len(original_subs)} legendas")
print(f"✅ Traduzido: {len(translated_subs)} legendas\n")

# Criar mapa original por ID
orig_map = {sub.id: sub for sub in original_subs}

# Correções manuais baseadas no que viste
corrections = {
    '664': '- talvez relacionado com-\n- Comam primeiro.',
    '665': 'Falem depois.',
    '666': 'Oh.',
    '667': 'Ei, rapazes, eles comeram-no!',
    '668': 'Olhem para as caras deles!',
    '669': 'Eu não como larvas.',
    '670': 'Hermano, arranja-me um scone.',
    '671': 'Está bem, está bem.',
    '672': 'Tampa metálica.',
}

print("🔧 A aplicar correções...\n")

# Aplicar correções
fixed_subs = []
for sub in translated_subs:
    if sub.id in corrections:
        print(f"✅ Corrigida {sub.id}: {corrections[sub.id][:40]}...")
        sub.text = corrections[sub.id]
    fixed_subs.append(sub)

# Guardar
output_path = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_SYNCED.srt'
output_content = generate_srt(fixed_subs)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output_content)

print(f"\n💾 Ficheiro guardado: {output_path}")
print("🎉 Re-sincronização concluída!")

# Verificar resultado
print("\n📋 Verificação (legendas 663-672):\n")
for sub in fixed_subs:
    if 663 <= int(sub.id) <= 672:
        orig = orig_map.get(sub.id)
        print(f"ID {sub.id}")
        print(f"  EN: {orig.text[:50] if orig else 'N/A'}...")
        print(f"  PT: {sub.text[:50]}...")
        print()
