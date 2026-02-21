#!/usr/bin/env python3
"""
Detecta todos os pontos onde há deslocamento de legendas
"""

import re
from pathlib import Path


def parse_srt(content):
    subtitles = []
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            id_line = lines[0].strip()
            timeframe = lines[1].strip()
            text = '\n'.join(lines[2:]).strip()
            subtitles.append({'id': id_line, 'timeframe': timeframe, 'text': text})
    return subtitles


print("🔍 Detecção de Deslocamentos\n")

# Ler ficheiro original (inglês)
with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt', 'r', encoding='utf-8') as f:
    original = parse_srt(f.read())

# Ler ficheiro traduzido ORIGINAL (antes da correção)
with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FIXED.srt', 'r', encoding='utf-8') as f:
    translated = parse_srt(f.read())

print(f"✅ Original: {len(original)} legendas")
print(f"✅ Traduzido: {len(translated)} legendas\n")

# Função simples de similaridade (primeiras palavras)
def are_similar(text1, text2):
    """Verifica se dois textos são similares (tradução um do outro)"""
    # Pegar primeiras 3 palavras de cada
    words1 = text1.lower().split()[:3]
    words2 = text2.lower().split()[:3]

    # Se um texto é muito curto (1-2 palavras), é difícil comparar
    if len(words1) < 2 or len(words2) < 2:
        return True  # Assumir correto para evitar falsos positivos

    # Verificar se há alguma palavra em comum
    common = set(words1) & set(words2)
    return len(common) > 0


# Detectar deslocamentos
print("🔍 A procurar deslocamentos...\n")

offsets_found = []
currently_offset = False
offset_start = None

for i in range(len(original)):
    orig = original[i]
    trans = translated[i]

    # Verificar se a tradução parece correta para este original
    # Comparar com a tradução atual e com a próxima

    current_match = are_similar(orig['text'], trans['text'])

    # Verificar se a próxima legenda traduzida corresponde melhor
    next_match = False
    if i + 1 < len(translated):
        next_trans = translated[i + 1]
        next_match = are_similar(orig['text'], next_trans['text'])

    # Se a próxima corresponde melhor que a atual, há deslocamento
    is_offset = next_match and not current_match

    if is_offset and not currently_offset:
        # Início de um deslocamento
        offset_start = int(orig['id'])
        currently_offset = True
        print(f"⚠️  Deslocamento detectado a partir de ID {orig['id']} ({orig['timeframe'].split(' --> ')[0]})")
        print(f"    EN: {orig['text'][:60]}...")
        print(f"    PT: {trans['text'][:60]}...")
        print(f"    PT seguinte: {next_trans['text'][:60]}...\n")

    elif not is_offset and currently_offset:
        # Fim de um deslocamento
        offset_end = int(original[i-1]['id'])
        offsets_found.append({'start': offset_start, 'end': offset_end})
        print(f"✅ Deslocamento terminou em ID {offset_end}")
        currently_offset = False
        offset_start = None

# Se ainda está deslocado no final
if currently_offset:
    offset_end = int(original[-1]['id'])
    offsets_found.append({'start': offset_start, 'end': offset_end})
    print(f"✅ Deslocamento continua até o fim (ID {offset_end})")

print("\n" + "="*70)
print(f"\n📊 Total de pontos de deslocamento encontrados: {len(offsets_found)}\n")

for i, offset in enumerate(offsets_found, 1):
    print(f"{i}. IDs {offset['start']} até {offset['end']}")

print("\n" + "="*70)
