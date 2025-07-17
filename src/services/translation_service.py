import logging
from typing import List, Dict, Any
from ..translation import TranslatorFactory
from ..subtitle import SRTParser
from config import settings
import os
import asyncio

logger = logging.getLogger(__name__)

class TranslationService:
    """Main service for handling subtitle translation workflow"""
    
    def __init__(self):
        self.srt_parser = SRTParser()
        self.translator = None
        self._initialize_translator()
    
    def _initialize_translator(self):
        """Initialize the translator based on configuration"""
        try:
            translator_config = {
                'api_key': settings.OPENAI_API_KEY,
                'model': settings.OPENAI_MODEL,
                'max_tokens': settings.OPENAI_MAX_TOKENS
            }
            
            self.translator = TranslatorFactory.create_translator('openai', translator_config)
            logger.info(f"Initialized translator: {self.translator.get_provider_name()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize translator: {str(e)}")
            raise Exception(f"Translator initialization failed: {str(e)}")
    
    async def translate_subtitle_file(self, input_file_path: str, output_file_path: str = None) -> str:
        """
        Translate a subtitle file from any language to Persian
        
        Args:
            input_file_path: Path to the input SRT file
            output_file_path: Path for the output file (optional)
            
        Returns:
            Path to the translated file
        """
        try:
            # Validate input file
            if not self.srt_parser.validate_srt_file(input_file_path):
                raise Exception("Invalid SRT file format")
            
            # Parse the SRT file
            logger.info(f"Parsing SRT file: {input_file_path}")
            subtitles = self.srt_parser.parse_file(input_file_path)
            
            if not subtitles:
                raise Exception("No subtitles found in the file")
            
            # Extract texts for translation
            texts_to_translate = [subtitle['text'] for subtitle in subtitles]
            
            # Translate texts
            logger.info(f"Translating {len(texts_to_translate)} subtitle entries")
            translated_texts = await self.translator.translate_batch(
                texts_to_translate, 
                settings.TARGET_LANGUAGE
            )
            
            # Update subtitles with translated texts
            for i, translated_text in enumerate(translated_texts):
                subtitles[i]['text'] = translated_text
                subtitles[i]['translated'] = True
            
            # Generate output file path if not provided
            if output_file_path is None:
                base_name = os.path.splitext(os.path.basename(input_file_path))[0]
                output_file_path = os.path.join(
                    settings.OUTPUT_DIR, 
                    f"{base_name}_persian.srt"
                )
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # Save translated file
            final_path = self.srt_parser.save_srt_file(subtitles, output_file_path)
            
            logger.info(f"Translation completed successfully: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Translation service failed: {str(e)}")
            raise Exception(f"Translation failed: {str(e)}")
    
    async def get_translation_preview(self, input_file_path: str, max_lines: int = 5) -> List[Dict[str, str]]:
        """
        Get a preview of translation for the first few lines
        
        Args:
            input_file_path: Path to the input SRT file
            max_lines: Maximum number of lines to preview
            
        Returns:
            List of dictionaries with original and translated text
        """
        try:
            # Parse the SRT file
            subtitles = self.srt_parser.parse_file(input_file_path)
            
            if not subtitles:
                return []
            
            # Get first few subtitles for preview
            preview_subtitles = subtitles[:max_lines]
            texts_to_translate = [subtitle['text'] for subtitle in preview_subtitles]
            
            # Translate preview texts
            translated_texts = await self.translator.translate_batch(
                texts_to_translate, 
                settings.TARGET_LANGUAGE
            )
            
            # Create preview result
            preview_result = []
            for i, subtitle in enumerate(preview_subtitles):
                preview_result.append({
                    'original': subtitle['text'],
                    'translated': translated_texts[i] if i < len(translated_texts) else subtitle['text'],
                    'time': f"{subtitle['start_time']} --> {subtitle['end_time']}"
                })
            
            return preview_result
            
        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            raise Exception(f"Preview failed: {str(e)}")
    
    def get_translator_info(self) -> Dict[str, Any]:
        """Get information about the current translator"""
        if self.translator:
            return {
                'provider': self.translator.get_provider_name(),
                'target_language': settings.TARGET_LANGUAGE,
                'available_providers': TranslatorFactory.get_available_providers()
            }
        return {'provider': 'None', 'error': 'Translator not initialized'}
    
    def change_translator(self, provider: str, config: Dict[str, Any]):
        """Change the translation provider"""
        try:
            self.translator = TranslatorFactory.create_translator(provider, config)
            logger.info(f"Changed translator to: {self.translator.get_provider_name()}")
        except Exception as e:
            logger.error(f"Failed to change translator: {str(e)}")
            raise Exception(f"Translator change failed: {str(e)}")