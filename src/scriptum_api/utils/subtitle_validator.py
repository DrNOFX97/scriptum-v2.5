"""
Subtitle quality validator
Detects common problems in SRT files
"""

import re
from typing import List, Dict, Any
from datetime import datetime, timedelta


def parse_timestamp(timestamp: str) -> timedelta:
    """Parse SRT timestamp to timedelta"""
    h, m, s_ms = timestamp.split(':')
    s, ms = s_ms.split(',')
    return timedelta(
        hours=int(h),
        minutes=int(m),
        seconds=int(s),
        milliseconds=int(ms)
    )


def format_timestamp(td: timedelta) -> str:
    """Format timedelta back to SRT timestamp"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def validate_subtitles(srt_content: str) -> Dict[str, Any]:
    """
    Validate subtitle quality based on PT-PT professional standards

    Standards based on Netflix PT-PT Style Guide and industry best practices:
    - Duration: 1-6 seconds (ideal 4-6s for 2 lines)
    - CPS: 12-15 ideal, 17 max
    - Characters/line: 32-37 ideal, 42-46 max
    - Lines: max 2
    - Gaps: min 2 frames (~80ms)

    Returns:
        {
            'total_entries': int,
            'problems': [
                {
                    'index': int,
                    'type': str,
                    'severity': str,  # 'error', 'warning', 'info'
                    'message': str,
                    'timecode': str,
                    'text': str,
                    'suggestion': str
                }
            ],
            'stats': {
                'long_durations': int,
                'long_lines': int,
                'long_pauses': int,
                'high_cps': int,
                'empty': int,
                'short_durations': int,
                'too_many_lines': int
            }
        }
    """

    # PT-PT Professional Standards
    MIN_DURATION = 1.0      # seconds
    MAX_DURATION = 6.0      # seconds
    WARN_DURATION = 5.0     # warn if approaching max

    IDEAL_CHARS = 37        # ideal chars/line
    MAX_CHARS = 42          # max acceptable (DVD standard)
    WARN_CHARS = 46         # warn if exceeding DVD standard

    IDEAL_CPS = 15          # characters per second
    MAX_CPS = 17            # max acceptable

    MAX_LINES = 2           # max lines per subtitle

    MIN_GAP = 0.08          # min gap between subtitles (2 frames @ 24fps)

    problems = []
    stats = {
        'long_durations': 0,
        'long_lines': 0,
        'long_pauses': 0,
        'high_cps': 0,
        'empty': 0,
        'short_durations': 0,
        'too_many_lines': 0
    }

    # Parse SRT
    entries = re.split(r'\n\n+', srt_content.strip())

    previous_end_time = None

    for i, entry in enumerate(entries):
        lines = entry.strip().split('\n')

        if len(lines) < 3:
            continue

        try:
            index = int(lines[0])
        except ValueError:
            continue

        timecode = lines[1]
        text = '\n'.join(lines[2:])

        # Parse times
        try:
            start_str, end_str = timecode.split(' --> ')
            start_time = parse_timestamp(start_str.strip())
            end_time = parse_timestamp(end_str.strip())
        except (ValueError, AttributeError):
            continue

        duration = (end_time - start_time).total_seconds()

        # Check 1: Duration (PT-PT: 1-6 seconds)
        if duration < MIN_DURATION:
            stats['short_durations'] += 1
            problems.append({
                'index': index,
                'type': 'short_duration',
                'severity': 'warning',
                'message': f'Duração muito curta: {duration:.1f}s (mín: {MIN_DURATION}s)',
                'timecode': timecode,
                'text': text,
                'suggestion': 'Aumentar duração para mínimo 1 segundo'
            })

        if duration > MAX_DURATION:
            stats['long_durations'] += 1
            severity = 'error' if duration > MAX_DURATION * 1.5 else 'warning'

            problems.append({
                'index': index,
                'type': 'long_duration',
                'severity': severity,
                'message': f'Duração muito longa: {duration:.1f}s (máx: {MAX_DURATION}s)',
                'timecode': timecode,
                'text': text,
                'suggestion': 'Dividir em 2+ legendas ou reduzir texto'
            })

        # Check 2: Line length (PT-PT: ideal 37, max 42, warn at 46)
        text_lines = text.split('\n')
        num_lines = len(text_lines)
        max_line_length = max(len(line) for line in text_lines) if text_lines else 0

        if num_lines > MAX_LINES:
            stats['too_many_lines'] += 1
            problems.append({
                'index': index,
                'type': 'too_many_lines',
                'severity': 'error',
                'message': f'{num_lines} linhas (máx: {MAX_LINES})',
                'timecode': timecode,
                'text': text,
                'suggestion': 'Dividir em múltiplas legendas ou condensar texto'
            })

        if max_line_length > WARN_CHARS:
            stats['long_lines'] += 1
            severity = 'error' if max_line_length > 50 else 'warning'

            problems.append({
                'index': index,
                'type': 'long_line',
                'severity': severity,
                'message': f'Linha muito longa: {max_line_length} chars (ideal: {IDEAL_CHARS}, máx: {MAX_CHARS})',
                'timecode': timecode,
                'text': text,
                'suggestion': 'Quebrar linha em ponto natural (vírgula, conjunção, pausa)'
            })

        # Check 3: CPS - Characters Per Second (PT-PT: ideal 12-15, max 17)
        total_chars = len(text.replace('\n', ''))
        cps = total_chars / duration if duration > 0 else 0

        if cps > MAX_CPS:
            stats['high_cps'] += 1
            severity = 'error' if cps > MAX_CPS * 1.2 else 'warning'

            problems.append({
                'index': index,
                'type': 'high_cps',
                'severity': severity,
                'message': f'CPS muito alto: {cps:.1f} chars/s (ideal: {IDEAL_CPS}, máx: {MAX_CPS})',
                'timecode': timecode,
                'text': text,
                'suggestion': 'Simplificar texto ou aumentar duração para leitura confortável'
            })

        # Check 4: Empty subtitle
        if not text.strip():
            stats['empty'] += 1

            problems.append({
                'index': index,
                'type': 'empty',
                'severity': 'error',
                'message': 'Legenda vazia',
                'timecode': timecode,
                'text': '',
                'suggestion': 'Remover entrada ou adicionar texto'
            })

        # Check 5: Gaps between subtitles
        if previous_end_time:
            gap = (start_time - previous_end_time).total_seconds()

            # Too small gap (< 2 frames @ 24fps)
            if gap < MIN_GAP and gap >= 0:
                problems.append({
                    'index': index,
                    'type': 'gap_too_small',
                    'severity': 'warning',
                    'message': f'Gap muito pequeno: {gap*1000:.0f}ms (mín: {MIN_GAP*1000:.0f}ms)',
                    'timecode': timecode,
                    'text': text,
                    'suggestion': 'Aumentar gap para mínimo 2 frames (~80ms)'
                })

            # Overlapping subtitles
            elif gap < 0:
                problems.append({
                    'index': index,
                    'type': 'overlap',
                    'severity': 'error',
                    'message': f'Sobreposição de {abs(gap):.2f}s com legenda anterior',
                    'timecode': timecode,
                    'text': text,
                    'suggestion': 'Ajustar timings para não sobrepor'
                })

            # Very long pause (might indicate missing subtitles)
            elif gap > 20:
                stats['long_pauses'] += 1
                severity = 'error' if gap > 60 else 'info'

                problems.append({
                    'index': index,
                    'type': 'long_pause',
                    'severity': severity,
                    'message': f'Pausa muito longa: {gap:.1f}s antes desta legenda',
                    'timecode': timecode,
                    'text': text,
                    'suggestion': 'Verificar se há diálogo em falta ou se a pausa é intencional'
                })

        previous_end_time = end_time

    return {
        'total_entries': len(entries),
        'problems': problems,
        'stats': stats,
        'has_problems': len(problems) > 0
    }
