#!/usr/bin/env python3
"""
Test script for subtitle validation system
Creates a test SRT file with known problems and validates it
"""

from src.scriptum_api.utils.subtitle_validator import validate_subtitles

# Test SRT content with various problems
test_srt = """1
00:00:01,000 --> 00:00:05,000
Normal subtitle - OK

2
00:00:06,000 --> 00:00:20,000
This subtitle is way too long - 14 seconds!
It should be split into multiple subtitles.

3
00:00:21,000 --> 00:00:25,000
This line is extremely long and has more than 42 characters which makes it hard to read on screen

4
00:00:26,000 --> 00:01:11,000
This one is REALLY long - 45 seconds!
Way too much time for a subtitle.

5
00:01:12,000 --> 00:01:15,000


6
00:01:16,000 --> 00:01:50,000
Long pause before this one - more than 20 seconds gap!

7
00:01:51,000 --> 00:01:53,000
This subtitle has way too many characters packed into a very short time making it impossible to read at a reasonable speed

8
00:01:54,000 --> 00:01:58,000
Normal subtitle again - OK

9
00:01:59,000 --> 00:02:03,000
Another normal one
"""

def main():
    print("=" * 70)
    print("🔍 Testing Subtitle Validation System")
    print("=" * 70)
    print()

    # Validate
    results = validate_subtitles(test_srt)

    # Print results
    print(f"Total entries: {results['total_entries']}")
    print(f"Has problems: {results['has_problems']}")
    print()

    # Stats
    print("Statistics:")
    for key, value in results['stats'].items():
        if value > 0:
            label = key.replace('_', ' ').title()
            print(f"  {label}: {value}")
    print()

    # Problems
    if results['problems']:
        print(f"Found {len(results['problems'])} problem(s):")
        print()

        for problem in results['problems']:
            severity_emoji = {
                'error': '🔴',
                'warning': '🟡',
                'info': '🔵'
            }.get(problem['severity'], '⚪')

            print(f"{severity_emoji} #{problem['index']} - {problem['type'].upper()}")
            print(f"   Timecode: {problem['timecode']}")
            print(f"   Message: {problem['message']}")
            print(f"   Suggestion: {problem['suggestion']}")
            print(f"   Text: {problem['text'][:50]}{'...' if len(problem['text']) > 50 else ''}")
            print()
    else:
        print("✅ No problems found!")

    print("=" * 70)
    print()

    # Expected problems:
    # - 2 long durations (14s, 45s)
    # - 1 long line (>42 chars)
    # - 1 high CPS (too many chars in short time)
    # - 1 empty subtitle
    # - 1 long pause (>20s gap)

    expected_problems = 6
    actual_problems = len(results['problems'])

    if actual_problems == expected_problems:
        print(f"✅ Test PASSED: Found {actual_problems} problems (expected {expected_problems})")
    else:
        print(f"⚠️  Test WARNING: Found {actual_problems} problems (expected {expected_problems})")

    print()

if __name__ == '__main__':
    main()
