#!/usr/bin/env python3
"""
Corrige AMBOS os deslocamentos:
- ID 664: shift +1 (legendas atrasadas)
- ID 1192: shift -1 (legendas adiantadas)
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


print("🔧 Correção de Ambos os Deslocamentos\n")
print("📖 A ler ficheiros...\n")

# Ler ficheiro original (inglês)
with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt', 'r', encoding='utf-8') as f:
    original_content = f.read()

# Ler ficheiro traduzido (com ambos deslocamentos)
with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FIXED.srt', 'r', encoding='utf-8') as f:
    translated_content = f.read()

original_subs = parse_srt(original_content)
translated_subs = parse_srt(translated_content)

print(f"✅ Original: {len(original_subs)} legendas")
print(f"✅ Traduzido: {len(translated_subs)} legendas\n")

# Criar mapas
orig_map = {sub.id: sub for sub in original_subs}
trans_map = {sub.id: sub for sub in translated_subs}

print("🔧 A corrigir deslocamentos...\n")

fixed_subs = []

for i, orig in enumerate(original_subs):
    current_id = orig.id
    current_id_num = int(current_id)

    # Legendas 1-663: OK
    if current_id_num < 664:
        trans = trans_map.get(current_id)
        if trans:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans.text))
        else:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

    # Legenda 664: corrigir manualmente (adicionar linha que falta)
    elif current_id_num == 664:
        trans_664 = trans_map.get('664')
        trans_665 = trans_map.get('665')

        text_664 = trans_664.text if trans_664 else ""
        text_665 = trans_665.text if trans_665 else ""

        # Juntar as duas
        if text_665.startswith('-'):
            combined = f"{text_664}\n{text_665}"
        else:
            combined = f"{text_664}\n- {text_665}"

        fixed_subs.append(Subtitle(orig.id, orig.timeframe, combined))
        if current_id_num == 664:
            print(f"✅ ID 664: corrigida (fundida com 665)")

    # Legendas 665-1196: shift +1 (pegar da próxima)
    elif 665 <= current_id_num <= 1196:
        next_id = str(current_id_num + 1)
        trans_next = trans_map.get(next_id)

        if trans_next:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_next.text))
            if current_id_num in [665, 1191, 1192]:
                print(f"✅ ID {current_id_num}: shift +1")
        else:
            trans_current = trans_map.get(current_id)
            if trans_current:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
            else:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

    # Legendas 1197-1199: shift -1 (pegar da anterior)
    elif 1197 <= current_id_num <= 1199:
        prev_id = str(current_id_num - 1)
        trans_prev = trans_map.get(prev_id)

        if trans_prev:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_prev.text))
            if current_id_num == 1197:
                print(f"✅ ID 1197: início shift -1")
        else:
            trans_current = trans_map.get(current_id)
            if trans_current:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
            else:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

    # Legenda 1200: sem shift (manter)
    elif current_id_num == 1200:
        trans_current = trans_map.get(current_id)
        if trans_current:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
            print(f"✅ ID 1200: mantida (sem shift)")
        else:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

    # Legendas 1201-1456: sem shift (manter como está)
    elif 1201 <= current_id_num <= 1456:
        trans_current = trans_map.get(current_id)
        if trans_current:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
            if current_id_num == 1201:
                print(f"✅ ID 1201: volta ao normal (sem shift)")
        else:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

    # Legenda 1457: correção manual
    elif current_id_num == 1457:
        fixed_subs.append(Subtitle(orig.id, orig.timeframe, "- Boa noite!\n- Cala-te tu!"))
        print(f"✅ ID 1457: corrigida manualmente")

    # Legenda 1458: manter (créditos)
    elif current_id_num == 1458:
        trans_current = trans_map.get(current_id)
        if trans_current:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
            print(f"✅ ID 1458: mantida (créditos)")
        else:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

print(f"\n✅ Total corrigido: {len(fixed_subs)} legendas")

# Guardar
output_path = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FINAL.srt'
output_content = generate_srt(fixed_subs)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output_content)

print(f"\n💾 Ficheiro guardado: {output_path}")
print("🎉 Correção completa!")

# Verificar alguns pontos-chave
print("\n📋 Verificação de pontos-chave:\n")

check_ids = ['663', '664', '665', '1191', '1192', '1193', '1200', '1457', '1458']
for check_id in check_ids:
    idx = int(check_id) - 1
    if idx < len(fixed_subs):
        o = original_subs[idx]
        f = fixed_subs[idx]
        print(f"ID {check_id}: EN=\"{o.text[:40]}...\" → PT=\"{f.text[:40]}...\"")
