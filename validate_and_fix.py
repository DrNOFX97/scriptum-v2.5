#!/usr/bin/env python3
"""
Valida e corrige ficheiro SRT traduzido
"""

import sys
from pathlib import Path
from translate import SRTParser, SubtitleValidator, Subtitle


def validate_and_fix(original_path: str, translated_path: str, output_path: str = None):
    """Valida e corrige ficheiro traduzido"""
    print("🔍 Validador e Corretor de Legendas SRT\n")

    # Ler ficheiros
    print(f"📖 A ler ficheiro original: {original_path}")
    with open(original_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    print(f"📖 A ler ficheiro traduzido: {translated_path}")
    with open(translated_path, 'r', encoding='utf-8') as f:
        translated_content = f.read()

    # Parse
    print("\n🔍 A analisar legendas...")
    original_subs = SRTParser.parse(original_content)
    translated_subs = SRTParser.parse(translated_content)

    print(f"✅ Original: {len(original_subs)} legendas")
    print(f"✅ Traduzido: {len(translated_subs)} legendas")

    # Validar
    print("\n🔍 A validar...")
    validator = SubtitleValidator()
    issues = validator.validate(original_subs, translated_subs)

    # Mostrar resultados
    print("\n" + "="*60)
    print("RESULTADOS DA VALIDAÇÃO")
    print("="*60)

    total_correct = len(original_subs)
    total_issues = 0

    # Timeframes
    timeframe_issues = len(issues['timeframe_mismatch'])
    if timeframe_issues == 0:
        print(f"✅ Timeframes: {total_correct}/{total_correct} corretos (100%)")
    else:
        print(f"❌ Timeframes: {timeframe_issues} diferentes")
        total_issues += timeframe_issues

    # Legendas em falta
    missing = len(issues['missing'])
    if missing > 0:
        print(f"❌ Legendas em falta: {missing}")
        total_issues += missing

    # Traduções vazias
    empty = len(issues['empty_translation'])
    if empty > 0:
        print(f"❌ Traduções vazias: {empty}")
        total_issues += empty

    # Quebras de linha
    line_issues = len(issues['line_rule_violations'])
    correct_lines = total_correct - line_issues
    line_percentage = (correct_lines / total_correct * 100) if total_correct > 0 else 0

    if line_issues == 0:
        print(f"✅ Regras de linha: {total_correct}/{total_correct} corretas (100%)")
    else:
        print(f"⚠️  Regras de linha: {correct_lines}/{total_correct} corretas ({line_percentage:.1f}%)")
        print(f"   {line_issues} legendas com regras de linha violadas")

    print("="*60)

    # Mostrar exemplos de problemas
    if line_issues > 0:
        print(f"\n📋 Primeiros 10 exemplos de regras de linha violadas:\n")
        for i, issue in enumerate(issues['line_rule_violations'][:10], 1):
            print(f"{i}. ID {issue['id']}")
            print(f"   Original:  \"{issue['original_text']}...\"")
            print(f"   Traduzido: \"{issue['translated_text']}...\"")
            print(f"   Corrigido: \"{issue['formatted_text']}...\"\n")

        if line_issues > 10:
            print(f"... e mais {line_issues - 10} problemas\n")

    # Corrigir se necessário
    if output_path and line_issues > 0:
        print(f"\n🔧 A corrigir quebras de linha...")
        fixed_subs = validator.fix_line_breaks(original_subs, translated_subs)

        # Validar novamente
        print("🔍 A validar correções...")
        issues_after = validator.validate(original_subs, fixed_subs)
        line_issues_after = len(issues_after['line_rule_violations'])

        improvement = line_issues - line_issues_after
        if improvement > 0:
            print(f"✅ Corrigidas {improvement} legendas ({improvement / line_issues * 100:.1f}%)")
        else:
            print("⚠️  Não foi possível corrigir automaticamente")

        # Guardar
        print(f"\n💾 A guardar ficheiro corrigido: {output_path}")
        output_content = SRTParser.generate(fixed_subs)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        file_size = Path(output_path).stat().st_size
        print(f"✅ Ficheiro criado com sucesso ({file_size} bytes)")
        print(f"\n🎉 Correção concluída!")

    elif line_issues > 0:
        print("\n💡 Para corrigir automaticamente, execute:")
        print(f"   python validate_and_fix.py {original_path} {translated_path} <output.srt>")

    return {
        'total': total_correct,
        'timeframe_correct': total_correct - timeframe_issues,
        'line_correct': correct_lines,
        'issues': issues
    }


def main():
    """Função principal"""
    if len(sys.argv) < 3:
        print("Uso:")
        print("  Validar:  python validate_and_fix.py <original.srt> <translated.srt>")
        print("  Corrigir: python validate_and_fix.py <original.srt> <translated.srt> <output.srt>")
        sys.exit(1)

    original_file = sys.argv[1]
    translated_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Verificar se ficheiros existem
    if not Path(original_file).exists():
        print(f"❌ Ficheiro não encontrado: {original_file}")
        sys.exit(1)

    if not Path(translated_file).exists():
        print(f"❌ Ficheiro não encontrado: {translated_file}")
        sys.exit(1)

    # Validar e corrigir
    try:
        validate_and_fix(original_file, translated_file, output_file)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
