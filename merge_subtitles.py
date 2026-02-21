#!/usr/bin/env python3
"""
Funde legendas específicas e re-numera as seguintes
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


def merge_subtitles(subtitles, ids_to_merge):
    """
    Funde múltiplas legendas numa só
    ids_to_merge: lista de IDs a fundir (ex: ['664', '665'])
    """
    # Encontrar índices das legendas a fundir
    indices = []
    for i, sub in enumerate(subtitles):
        if sub.id in ids_to_merge:
            indices.append(i)

    if len(indices) != len(ids_to_merge):
        print(f"⚠️  Aviso: Encontrados {len(indices)} de {len(ids_to_merge)} IDs")

    # Ordenar índices
    indices.sort()

    # Criar legenda fundida
    first_idx = indices[0]
    last_idx = indices[-1]

    # Timeframe: início da primeira até fim da última
    start_time = subtitles[first_idx].timeframe.split('-->')[0].strip()
    end_time = subtitles[last_idx].timeframe.split('-->')[1].strip()
    merged_timeframe = f"{start_time} --> {end_time}"

    # Texto: juntar todos os textos
    merged_text = '\n'.join([subtitles[i].text for i in indices])

    # Criar nova legenda
    merged_sub = Subtitle(subtitles[first_idx].id, merged_timeframe, merged_text)

    # Criar nova lista sem as legendas fundidas, substituindo pela fundida
    new_subtitles = []

    for i, sub in enumerate(subtitles):
        if i == first_idx:
            # Adicionar legenda fundida
            new_subtitles.append(merged_sub)
        elif i not in indices:
            # Manter legenda original
            new_subtitles.append(sub)
        # Ignorar outras legendas que foram fundidas

    # Re-numerar
    for i, sub in enumerate(new_subtitles):
        sub.id = str(i + 1)

    return new_subtitles


def generate_srt(subtitles):
    """Gera conteúdo SRT"""
    content = []
    for sub in subtitles:
        content.append(f"{sub.id}\n{sub.timeframe}\n{sub.text}\n")
    return '\n'.join(content).strip()


def main():
    if len(sys.argv) < 4:
        print("Uso: python merge_subtitles.py <input.srt> <output.srt> <id1> <id2> [id3...]")
        print("\nExemplo:")
        print("  python merge_subtitles.py input.srt output.srt 664 665")
        print("\n  Isto vai fundir as legendas 664 e 665 numa só")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    ids_to_merge = sys.argv[3:]

    print(f"🔧 Fusão de Legendas SRT\n")
    print(f"📖 Ficheiro: {input_file}")
    print(f"🔗 A fundir legendas: {', '.join(ids_to_merge)}\n")

    # Ler ficheiro
    if not Path(input_file).exists():
        print(f"❌ Ficheiro não encontrado: {input_file}")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse
    subtitles = parse_srt(content)
    print(f"✅ {len(subtitles)} legendas encontradas")

    # Mostrar legendas a fundir
    print(f"\n📝 Legendas a fundir:\n")
    for sub in subtitles:
        if sub.id in ids_to_merge:
            print(f"ID {sub.id}")
            print(f"  {sub.timeframe}")
            print(f"  {sub.text}")
            print()

    # Fundir
    merged_subtitles = merge_subtitles(subtitles, ids_to_merge)

    print(f"✅ Resultado: {len(merged_subtitles)} legendas (era {len(subtitles)})")
    print(f"   Redução: {len(subtitles) - len(merged_subtitles)} legenda(s)")

    # Mostrar legenda fundida
    print(f"\n🔗 Legenda fundida:\n")
    for sub in merged_subtitles:
        if sub.id == ids_to_merge[0]:  # Mostrar a legenda com o primeiro ID
            print(f"ID {sub.id}")
            print(f"  {sub.timeframe}")
            print(f"  {sub.text}")
            print()

    # Gerar e guardar
    output_content = generate_srt(merged_subtitles)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)

    file_size = Path(output_file).stat().st_size
    print(f"\n💾 Ficheiro guardado: {output_file}")
    print(f"   Tamanho: {file_size} bytes")
    print(f"\n🎉 Fusão concluída!")


if __name__ == '__main__':
    main()
