#!/usr/bin/env python3
"""
Re-sincroniza todas as legendas a partir da 664 até ao fim
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


print("🔧 Re-sincronização Completa\n")
print("📖 A ler ficheiros...\n")

# Ler ficheiro original (inglês)
with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia.2.2025.1440p.DCP.WEBRIP.AC3.SDR.H264.srt', 'r', encoding='utf-8') as f:
    original_content = f.read()

# Ler ficheiro traduzido (com deslocamento)
with open('/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_FIXED.srt', 'r', encoding='utf-8') as f:
    translated_content = f.read()

original_subs = parse_srt(original_content)
translated_subs = parse_srt(translated_content)

print(f"✅ Original: {len(original_subs)} legendas")
print(f"✅ Traduzido: {len(translated_subs)} legendas\n")

# Criar mapas
orig_map = {sub.id: sub for sub in original_subs}
trans_map = {sub.id: sub for sub in translated_subs}

# Estratégia:
# - Legendas 1-663: manter como estão (corretas)
# - Legenda 664: corrigir manualmente (adicionar "Comam primeiro")
# - Legendas 665-fim: pegar texto da legenda SEGUINTE (665 pega de 666, 666 pega de 667, etc.)

print("🔧 A re-sincronizar...\n")

fixed_subs = []

for i, orig in enumerate(original_subs):
    current_id = orig.id
    current_id_num = int(current_id)

    # Legendas antes de 664: manter tradução original
    if current_id_num < 664:
        trans = trans_map.get(current_id)
        if trans:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans.text))
        else:
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

    # Legenda 664: corrigir manualmente
    elif current_id_num == 664:
        # Original: "- perhaps pertaining to-\n- Eat first."
        # Tradução correta: "- talvez relacionado com-\n- Comam primeiro."
        trans_664 = trans_map.get('664')
        trans_665 = trans_map.get('665')

        # 664 tem "talvez relacionado com-", 665 tem "Comam primeiro"
        # Juntar as duas
        text_664 = trans_664.text if trans_664 else ""
        text_665 = trans_665.text if trans_665 else ""

        # Se text_665 já começa com "-", não adicionar outro
        if text_665.startswith('-'):
            combined = f"{text_664}\n{text_665}"
        else:
            combined = f"{text_664}\n- {text_665}"

        fixed_subs.append(Subtitle(orig.id, orig.timeframe, combined))
        print(f"✅ Corrigida 664: {combined[:40]}...")

    # Legendas 665 em diante: pegar texto da legenda seguinte na tradução
    else:
        # Legenda 1457: correção manual (tradução incompleta)
        if current_id_num == 1457:
            # Original: "- Good night!\n- You shut up!"
            # Tradução correta: "- Boa noite!\n- Cala-te tu!"
            fixed_subs.append(Subtitle(orig.id, orig.timeframe, "- Boa noite!\n- Cala-te tu!"))
            print(f"✅ Legenda 1457: corrigida manualmente")
        # Última legenda (1458): manter como está (já está correta)
        elif current_id_num == 1458:
            trans_current = trans_map.get(current_id)
            if trans_current:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
                print(f"✅ Legenda 1458: mantida (créditos)")
            else:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))
        else:
            # Pegar texto da legenda N+1 na tradução
            next_id = str(current_id_num + 1)
            trans_next = trans_map.get(next_id)

            if trans_next:
                fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_next.text))
                if current_id_num <= 672 or current_id_num >= 1454:  # Mostrar primeiras e últimas correções
                    print(f"✅ Legenda {current_id}: texto de {next_id} → {trans_next.text[:40]}...")
            else:
                # Se não houver próxima legenda, usar a atual
                trans_current = trans_map.get(current_id)
                if trans_current:
                    fixed_subs.append(Subtitle(orig.id, orig.timeframe, trans_current.text))
                else:
                    # Fallback: manter original em inglês
                    fixed_subs.append(Subtitle(orig.id, orig.timeframe, orig.text))

print(f"\n✅ Re-sincronizadas {len(fixed_subs)} legendas")

# Guardar
output_path = '/Users/f.nuno/Downloads/Zootopia 2/Zootopia2_PT-PT_RESYNCED.srt'
output_content = generate_srt(fixed_subs)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output_content)

print(f"\n💾 Ficheiro guardado: {output_path}")
print("🎉 Re-sincronização completa concluída!")

# Verificar resultado
print("\n📋 Verificação (legendas 663-672):\n")
for sub in fixed_subs:
    if 663 <= int(sub.id) <= 672:
        orig = orig_map.get(sub.id)
        print(f"ID {sub.id}")
        print(f"  {sub.timeframe}")
        print(f"  EN: {orig.text[:60] if orig else 'N/A'}...")
        print(f"  PT: {sub.text[:60]}...")
        print()
