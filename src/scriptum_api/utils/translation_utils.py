#!/usr/bin/env python3
"""
Tradutor de Legendas SRT - EN para PT-PT
Com validação e correção automática
"""

import re
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
import requests

# =============================================================================
# Line formatting rules
# =============================================================================

MAX_LINE_LENGTH = 42
DIALOGUE_DASH_RE = re.compile(r'^\s*[-–—]')
TAG_RE = re.compile(r'<[^>]+>')
LITERAL_BREAK_RE = re.compile(r'(\\n|/n)', re.IGNORECASE)
SPACED_ELLIPSES_RE = re.compile(r'\.\s+\.\s+\.')
MULTI_SPACE_RE = re.compile(r'[ \t]{2,}')


class Subtitle:
    """Representa uma legenda SRT"""
    def __init__(self, id: str, timeframe: str, text: str):
        self.id = id
        self.timeframe = timeframe
        self.text = text
        self.line_count = len(text.split('\n'))

    def __repr__(self):
        return f"Subtitle({self.id}, {self.timeframe}, {self.line_count} lines)"


class SRTParser:
    """Parser e gerador de ficheiros SRT"""

    @staticmethod
    def parse(content: str) -> List[Subtitle]:
        """Parse conteúdo SRT"""
        subtitles = []
        blocks = re.split(r'\n\s*\n', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            id_line = lines[0].strip()
            timeframe = lines[1].strip()
            text = '\n'.join(lines[2:]).strip()

            if SRTParser.is_valid_timeframe(timeframe):
                subtitles.append(Subtitle(id_line, timeframe, text))

        return subtitles

    @staticmethod
    def is_valid_timeframe(timeframe: str) -> bool:
        """Valida formato do timeframe"""
        pattern = r'^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}$'
        return bool(re.match(pattern, timeframe))

    @staticmethod
    def generate(subtitles: List[Subtitle]) -> str:
        """Gera conteúdo SRT"""
        content = []
        for sub in subtitles:
            content.append(f"{sub.id}\n{sub.timeframe}\n{sub.text}\n")
        return '\n'.join(content).strip()


class SubtitleFormatter:
    """Aplica regras de formatação de linhas nas legendas"""

    @staticmethod
    def _visible_len(text: str) -> int:
        return len(TAG_RE.sub('', text))

    @staticmethod
    def _normalize_line(line: str) -> str:
        line = LITERAL_BREAK_RE.sub(' ', line)
        line = SPACED_ELLIPSES_RE.sub('...', line)
        line = MULTI_SPACE_RE.sub(' ', line)
        return line.strip()

    @classmethod
    def _normalize_lines(cls, text: str) -> List[str]:
        if not text:
            return []
        lines = [cls._normalize_line(l) for l in text.split('\n')]
        return [l for l in lines if l]

    @staticmethod
    def _is_dialogue(text: str) -> bool:
        if not text:
            return False
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        dash_lines = sum(1 for l in lines if DIALOGUE_DASH_RE.match(l))
        return dash_lines >= 2

    @staticmethod
    def _ensure_dash(line: str) -> str:
        if not line:
            return line
        if DIALOGUE_DASH_RE.match(line):
            return line
        return f"- {line.lstrip()}"

    @classmethod
    def _split_on_second_dash(cls, text: str) -> Tuple[str, str]:
        if not text:
            return ('', '')
        stripped = text.strip()
        if not stripped or not DIALOGUE_DASH_RE.match(stripped):
            return ('', '')

        for sep in (" - ", " – ", " — "):
            idx = stripped.find(sep, 2)
            if idx != -1:
                line1 = stripped[:idx].strip()
                line2 = stripped[idx + len(sep):].strip()
                if line2 and not DIALOGUE_DASH_RE.match(line2):
                    line2 = f"- {line2}"
                return (line1, line2)

        return ('', '')

    @classmethod
    def _best_split(cls, text: str) -> Tuple[str, str]:
        words = text.split()
        if len(words) < 2:
            return (text, '')

        best = None
        for i in range(1, len(words)):
            l1 = ' '.join(words[:i])
            l2 = ' '.join(words[i:])
            v1 = cls._visible_len(l1)
            v2 = cls._visible_len(l2)
            both_fit = v1 <= MAX_LINE_LENGTH and v2 <= MAX_LINE_LENGTH
            score = (
                0 if both_fit else 1,
                max(v1, v2),
                abs(v1 - v2),
            )
            if best is None or score < best[0]:
                best = (score, l1, l2)

        if best is None:
            return (text, '')
        return (best[1], best[2])

    @classmethod
    def _format_dialogue(cls, raw_text: str, normalized_text: str) -> str:
        lines = cls._normalize_lines(raw_text)

        if len(lines) >= 2:
            line1 = lines[0]
            line2 = ' '.join(lines[1:]).strip()
        else:
            line1, line2 = cls._split_on_second_dash(normalized_text)
            if not line1 and not line2:
                line1, line2 = cls._best_split(normalized_text)

        line1 = cls._ensure_dash(line1)
        line2 = cls._ensure_dash(line2) if line2 else ''

        if not line2:
            return line1
        return f"{line1}\n{line2}"

    @classmethod
    def _format_non_dialogue(cls, text: str) -> str:
        if cls._visible_len(text) <= MAX_LINE_LENGTH:
            return text

        line1, line2 = cls._best_split(text)
        if not line2:
            return text
        return f"{line1}\n{line2}"

    @classmethod
    def format_text(cls, text: str, original_text: str = '') -> str:
        if not text:
            return ''

        lines = cls._normalize_lines(text)
        normalized = ' '.join(lines).strip()
        normalized = MULTI_SPACE_RE.sub(' ', normalized)

        if not normalized:
            return ''

        if cls._is_dialogue(original_text) or cls._is_dialogue(text):
            return cls._format_dialogue(text, normalized)

        return cls._format_non_dialogue(normalized)


class GeminiTranslator:
    """Tradutor usando Google Gemini API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
        self.batch_size = 10
        self.max_retries = 3
        self.retry_delay = 2

    def translate_batch(self, subtitles: List[Subtitle], progress_callback=None) -> List[Subtitle]:
        """Traduz lote de legendas"""
        translated = []
        total_batches = (len(subtitles) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(subtitles), self.batch_size):
            batch = subtitles[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            if progress_callback:
                progress_callback(i, len(subtitles), batch_num, total_batches)

            # Traduzir com retry
            for retry in range(self.max_retries):
                try:
                    translated_batch = self._translate_texts(batch)
                    translated.extend(translated_batch)
                    break
                except Exception as e:
                    if retry < self.max_retries - 1:
                        print(f"   ⚠️  Erro no lote {batch_num}, tentativa {retry + 1}/{self.max_retries}...")
                        time.sleep(self.retry_delay)
                    else:
                        raise Exception(f"Falha após {self.max_retries} tentativas: {e}")

            # Pausa entre batches
            time.sleep(0.5)

        return translated

    def _translate_texts(self, subtitles: List[Subtitle]) -> List[Subtitle]:
        """Traduz um lote de legendas"""
        texts = [sub.text for sub in subtitles]
        prompt = self._build_prompt(texts)

        response = requests.post(
            f"{self.api_url}?key={self.api_key}",
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'temperature': 0.3,
                    'topK': 40,
                    'topP': 0.95,
                    'maxOutputTokens': 8192,
                }
            },
            timeout=30
        )

        if not response.ok:
            error_data = response.json()
            raise Exception(f"Erro da API: {error_data.get('error', {}).get('message', response.text)}")

        data = response.json()
        translated_text = data['candidates'][0]['content']['parts'][0]['text']

        # Parse traduções
        translations = self._parse_translation(translated_text, len(texts))

        # Criar novos Subtitles com traduções
        translated_subs = []
        for i, sub in enumerate(subtitles):
            if i < len(translations):
                translated_subs.append(Subtitle(sub.id, sub.timeframe, translations[i]))
            else:
                # Fallback: manter original se não houver tradução
                translated_subs.append(Subtitle(sub.id, sub.timeframe, sub.text))

        return translated_subs

    def _build_prompt(self, texts: List[str]) -> str:
        """Constrói prompt para tradução"""
        numbered = '\n'.join([f"{i+1}. {text}" for i, text in enumerate(texts)])

        return f"""Traduza as seguintes legendas de INGLÊS para PORTUGUÊS DE PORTUGAL (PT-PT).

CONTEXTO: Filme de animação "Zootopia" (em Portugal: "Zootrópolis")

REGRAS IMPORTANTES:
- Use português de Portugal (PT-PT), não brasileiro
- Use SEMPRE a segunda pessoa (tu/você) nas falas, nunca a terceira pessoa
- Linguagem adequada para desenhos animados (clara, direta, expressiva)
- "Zootopia" deve ser traduzido como "Zootrópolis"
- Máximo de 2 linhas por legenda
- Usa 1 linha sempre que o texto couber numa única linha
- Usa 2 linhas apenas quando o texto for longo, equilibrando as duas linhas
- Diálogos com dois locutores ficam sempre em 2 linhas, cada linha começando por "-"
- Não uses "\\n" ou "/n" literais; usa quebras reais apenas quando necessário
- Reticências sempre juntas: "..." (nunca ".  .  .")
- Preserve tags HTML se existirem (como <i>, <b>, etc.)
- Mantenha a numeração exata
- Não adicione comentários ou explicações
- Retorne apenas as traduções numeradas
- Tom adequado para filme familiar/infantil
- Não exceda 2 linhas por legenda

LEGENDAS A TRADUZIR:
{numbered}

TRADUÇÕES (mantenha a numeração):"""

    def _parse_translation(self, text: str, expected_count: int) -> List[str]:
        """Parse resposta da tradução"""
        translations = []

        # Dividir por blocos numerados
        blocks = re.split(r'\n(?=\d+\.\s)', text)

        for block in blocks:
            match = re.match(r'^\d+\.\s*(.+)$', block, re.DOTALL)
            if match:
                translations.append(match.group(1).strip())

        return translations


class SubtitleValidator:
    """Valida e corrige legendas traduzidas"""

    @staticmethod
    def validate(original: List[Subtitle], translated: List[Subtitle]) -> Dict:
        """Valida legendas traduzidas"""
        issues = {
            'missing': [],
            'timeframe_mismatch': [],
            'line_rule_violations': [],
            'empty_translation': []
        }

        # Criar mapa de traduções por ID
        trans_map = {sub.id: sub for sub in translated}

        for orig in original:
            trans = trans_map.get(orig.id)

            if not trans:
                issues['missing'].append(orig.id)
                continue

            if orig.timeframe != trans.timeframe:
                issues['timeframe_mismatch'].append({
                    'id': orig.id,
                    'original': orig.timeframe,
                    'translated': trans.timeframe
                })

            if not trans.text or len(trans.text.strip()) < 2:
                issues['empty_translation'].append({
                    'id': orig.id,
                    'original_text': orig.text
                })

            formatted = SubtitleFormatter.format_text(trans.text, orig.text)
            if formatted != trans.text:
                issues['line_rule_violations'].append({
                    'id': orig.id,
                    'original_text': orig.text[:60],
                    'translated_text': trans.text[:60],
                    'formatted_text': formatted[:60]
                })

        return issues

    @staticmethod
    def fix_line_breaks(original: List[Subtitle], translated: List[Subtitle]) -> List[Subtitle]:
        """Aplica regras de linha nas traduções"""
        fixed = []
        trans_map = {sub.id: sub for sub in translated}

        for orig in original:
            trans = trans_map.get(orig.id)

            if not trans:
                fixed.append(Subtitle(orig.id, orig.timeframe, orig.text))
                continue

            fixed_text = SubtitleFormatter.format_text(trans.text, orig.text)
            fixed.append(Subtitle(orig.id, orig.timeframe, fixed_text))

        return fixed

    @staticmethod
    def _redistribute_lines(text: str, target_lines: int) -> str:
        """Redistribui texto em N linhas"""
        # Remover quebras existentes
        clean_text = text.replace('\n', ' ')

        # Se for apenas 1 linha, retornar como está
        if target_lines == 1:
            return clean_text

        # Dividir palavras
        words = clean_text.split()
        if not words:
            return text

        # Calcular palavras por linha
        words_per_line = len(words) // target_lines
        remainder = len(words) % target_lines

        lines = []
        pos = 0

        for i in range(target_lines):
            # Adicionar palavras extras às primeiras linhas
            count = words_per_line + (1 if i < remainder else 0)
            line_words = words[pos:pos + count]
            lines.append(' '.join(line_words))
            pos += count

        return '\n'.join(lines)


class SubtitleTranslator:
    """Classe principal para tradução completa"""

    def __init__(self, api_key: str):
        self.translator = GeminiTranslator(api_key)
        self.validator = SubtitleValidator()

    def translate_file(self, input_path: str, output_path: str, auto_fix: bool = True) -> Dict:
        """Traduz ficheiro SRT completo com validação e correção"""
        print("🎬 Tradutor de Legendas SRT - EN para PT-PT\n")

        # Ler ficheiro original
        print(f"📖 A ler ficheiro: {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse
        print("🔍 A analisar legendas...")
        original_subs = SRTParser.parse(content)
        print(f"✅ {len(original_subs)} legendas encontradas\n")

        # Traduzir
        print(f"🌐 A traduzir {len(original_subs)} legendas...\n")
        translated_subs = self.translator.translate_batch(
            original_subs,
            progress_callback=self._progress_callback
        )

        print(f"\n✅ Recebidas {len(translated_subs)} traduções de {len(original_subs)} legendas")

        # Validar
        print("\n🔍 A validar tradução...")
        issues = self.validator.validate(original_subs, translated_subs)

        self._print_validation_results(issues)

        # Corrigir se necessário
        final_subs = translated_subs
        if auto_fix and issues['line_rule_violations']:
            print(f"\n🔧 A aplicar regras de linhas em {len(issues['line_rule_violations'])} legendas...")
            final_subs = self.validator.fix_line_breaks(original_subs, translated_subs)

            # Validar novamente
            print("🔍 A validar correções...")
            issues_after_fix = self.validator.validate(original_subs, final_subs)

            improvement = len(issues['line_rule_violations']) - len(issues_after_fix['line_rule_violations'])
            print(f"✅ Corrigidas {improvement} legendas ({improvement / len(issues['line_rule_violations']) * 100:.1f}%)")

        # Guardar
        print(f"\n💾 A guardar ficheiro traduzido: {output_path}")
        output_content = SRTParser.generate(final_subs)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        file_size = Path(output_path).stat().st_size
        print(f"✅ Ficheiro criado com sucesso ({file_size} bytes)")
        print(f"\n🎉 Tradução concluída!")

        return {
            'total': len(original_subs),
            'translated': len(final_subs),
            'issues': issues
        }

    def _progress_callback(self, current: int, total: int, batch: int, total_batches: int):
        """Callback de progresso"""
        percentage = int((current / total) * 100)
        print(f"   Lote {batch}/{total_batches} ({percentage}%)")

    def _print_validation_results(self, issues: Dict):
        """Imprime resultados da validação"""
        total_issues = sum(len(v) for v in issues.values())

        if total_issues == 0:
            print("✅ Nenhum problema encontrado!")
            return

        print(f"\n⚠️  Encontrados {total_issues} problemas:")

        if issues['missing']:
            print(f"   - Legendas em falta: {len(issues['missing'])}")

        if issues['timeframe_mismatch']:
            print(f"   - Timeframes diferentes: {len(issues['timeframe_mismatch'])}")

        if issues['empty_translation']:
            print(f"   - Traduções vazias: {len(issues['empty_translation'])}")

        if issues['line_rule_violations']:
            print(f"   - Regras de linhas violadas: {len(issues['line_rule_violations'])}")

            # Mostrar primeiros 5 exemplos
            if issues['line_rule_violations']:
                print("\n   Exemplos:")
                for issue in issues['line_rule_violations'][:5]:
                    print(f"      ID {issue['id']}")


def main():
    """Função principal"""
    if len(sys.argv) < 3:
        print("Uso: python translate.py <input.srt> <output.srt> [--no-fix]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    auto_fix = '--no-fix' not in sys.argv

    # API Key
    api_key = 'AIzaSyCl8KmWN8aE1o9gX1BzE8SJpdmzF21tp2c'

    # Verificar se ficheiro existe
    if not Path(input_file).exists():
        print(f"❌ Ficheiro não encontrado: {input_file}")
        sys.exit(1)

    # Traduzir
    translator = SubtitleTranslator(api_key)
    try:
        results = translator.translate_file(input_file, output_file, auto_fix)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
