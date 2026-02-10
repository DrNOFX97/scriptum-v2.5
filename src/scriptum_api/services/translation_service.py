"""
Translation service
Handles subtitle translation using Google Gemini API with existing translate.py module
"""
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing translation module (now in utils)
from ..utils.translation_utils import SRTParser, GeminiTranslator, SubtitleValidator, Subtitle


class TranslationService:
    """Service for subtitle translation"""

    def __init__(self, api_key: str, batch_size: int = 10):
        """
        Initialize translation service

        Args:
            api_key: Google Gemini API key
            batch_size: Number of subtitles per batch
        """
        self.api_key = api_key
        self.batch_size = batch_size
        self.translator = GeminiTranslator(api_key) if api_key else None
        self.validator = SubtitleValidator()

    def translate_file(
        self,
        input_path: Path,
        output_path: Path,
        source_lang: str,
        target_lang: str,
        movie_context: Optional[str] = None
    ) -> bool:
        """
        Translate subtitle file

        Args:
            input_path: Input SRT file path
            output_path: Output SRT file path
            source_lang: Source language code (en, pt)
            target_lang: Target language code (en, pt)
            movie_context: Optional movie name for context

        Returns:
            True if successful
        """
        if not self.translator:
            print("⚠️  Gemini API key not configured")
            return False

        try:
            print(f"\n{'='*70}")
            print(f"🌐 Translating: {input_path.name}")
            print(f"   {source_lang.upper()} → {target_lang.upper()}")
            if movie_context:
                print(f"   Context: {movie_context}")
            print(f"{'='*70}\n")

            # Parse original subtitles
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_subs = SRTParser.parse(content)
            print(f"📝 Parsed {len(original_subs)} subtitle entries")

            # Translate in batches
            translated_subs = []
            total_batches = (len(original_subs) + self.batch_size - 1) // self.batch_size

            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(original_subs))
                batch = original_subs[start_idx:end_idx]

                print(f"🔄 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} items)...")

                # Translate batch (GeminiTranslator expects Subtitle objects)
                translated_batch = self.translator._translate_texts(batch)
                translated_subs.extend(translated_batch)

                print(f"✅ Batch {batch_num + 1} complete")

            # Validate and fix line breaks
            print("\n🔍 Validating translations...")
            issues = self.validator.validate(original_subs, translated_subs)

            if issues['line_rule_violations']:
                print("⚠️  Line rule violations detected, applying fixes...")
                translated_subs = self.validator.fix_line_breaks(original_subs, translated_subs)
                print("✅ Fixes applied")

            # Generate output file
            output_content = SRTParser.generate(translated_subs)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)

            print(f"\n✅ Translation complete: {output_path.name}")
            print(f"   Total entries: {len(translated_subs)}")
            print(f"{'='*70}\n")

            return True

        except Exception as e:
            print(f"❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def translate_text(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        movie_context: Optional[str] = None
    ) -> List[str]:
        """
        Translate list of texts

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            movie_context: Optional movie context

        Returns:
            List of translated texts
        """
        if not self.translator:
            print("⚠️  Gemini API key not configured")
            return texts

        try:
            # Wrap texts into temporary Subtitle objects
            temp = [
                Subtitle(str(i + 1), "00:00:00,000 --> 00:00:01,000", text)
                for i, text in enumerate(texts)
            ]
            translated = self.translator._translate_texts(temp)
            return [sub.text for sub in translated]
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return texts

    @staticmethod
    def get_supported_languages() -> List[str]:
        """Get list of supported languages"""
        return ['en', 'pt']

    @staticmethod
    def validate_language(lang: str) -> bool:
        """Validate if language is supported"""
        return lang in TranslationService.get_supported_languages()

    def get_stats(self, original_subs: List[Dict], translated_subs: List[Dict]) -> Dict[str, Any]:
        """
        Get translation statistics

        Args:
            original_subs: Original subtitles
            translated_subs: Translated subtitles

        Returns:
            Statistics dictionary
        """
        original_chars = sum(len(sub.text) for sub in original_subs)
        translated_chars = sum(len(sub.text) for sub in translated_subs)

        original_words = sum(len(sub.text.split()) for sub in original_subs)
        translated_words = sum(len(sub.text.split()) for sub in translated_subs)

        return {
            'total_entries': len(translated_subs),
            'original_characters': original_chars,
            'translated_characters': translated_chars,
            'original_words': original_words,
            'translated_words': translated_words,
            'expansion_ratio': round(translated_chars / original_chars, 2) if original_chars > 0 else 1.0
        }
