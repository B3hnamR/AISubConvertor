import logging
from typing import List, Dict, Any
from ..translation import TranslatorFactory
from ..subtitle import SRTParser, SubtitleTimingManager
from ..utils import get_file_manager
from config import settings
import os
import asyncio

logger = logging.getLogger(__name__)

class TranslationService:
    """Main service for handling subtitle translation workflow with file management"""
    
    def __init__(self):
        self.srt_parser = SRTParser()
        self.timing_manager = SubtitleTimingManager()
        self.file_manager = get_file_manager(settings.TEMP_DIR, settings.MAX_FILE_SIZE_MB)
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
    
    # متدهای مدیریت فایل
    
    async def can_user_upload(self, user_id: int) -> bool:
        """بررسی امکان آپلود فایل برای کاربر"""
        return await self.file_manager.can_upload_file(user_id)
    
    async def prepare_file_upload(self, user_id: int, filename: str, file_size: int) -> Dict[str, Any]:
        """آماده‌سازی آپلود فایل"""
        return await self.file_manager.prepare_user_upload(user_id, filename, file_size)
    
    async def process_user_file(self, user_id: int, file_path: str) -> str:
        """
        پردازش کامل فایل کاربر با مدیریت تایمینگ دقیق
        
        Args:
            user_id: شناسه کاربر
            file_path: مسیر فایل دانلود شده
            
        Returns:
            مسیر فایل ترجمه شده
        """
        try:
            # شروع پردازش
            await self.file_manager.start_file_processing(user_id)
            
            # اعتبارسنجی فایل
            if not self.srt_parser.validate_srt_file(file_path):
                raise Exception("فرمت فایل SRT نامعتبر است")
            
            # تجزیه فایل با حفظ تایمینگ دقیق
            logger.info(f"Parsing SRT file for user {user_id}: {file_path}")
            original_subtitles = self.srt_parser.parse_file(file_path)
            
            if not original_subtitles:
                raise Exception("هیچ زیرنویسی در فایل یافت نشد")
            
            # استخراج متن‌ها برای ترجمه
            texts_to_translate = [subtitle['text'] for subtitle in original_subtitles]
            
            # ترجمه متن‌ها
            logger.info(f"Translating {len(texts_to_translate)} subtitle entries for user {user_id}")
            translated_texts = await self.translator.translate_batch(
                texts_to_translate, 
                settings.TARGET_LANGUAGE
            )
            
            # حفظ تایمینگ اصلی در ترجمه
            translated_subtitles = self.timing_manager.preserve_timing_in_translation(
                original_subtitles, 
                translated_texts
            )
            
            # تولید مسیر فایل خروجی
            file_info = await self.file_manager.get_user_file_info(user_id)
            if not file_info:
                raise Exception("اطلاعات فایل کاربر یافت نشد")
            
            base_name = os.path.splitext(file_info['original_filename'])[0]
            output_file_path = os.path.join(
                settings.OUTPUT_DIR,
                f"user_{user_id}",
                f"{base_name}_persian.srt"
            )
            
            # ایجاد دایرکتوری خروجی
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # ذخیره فایل ترجمه شده
            final_path = self.srt_parser.save_srt_file(translated_subtitles, output_file_path)
            
            # تکمیل پردازش
            await self.file_manager.complete_file_processing(user_id, final_path)
            
            # تحلیل آماری نهایی
            timing_stats = self.timing_manager.analyze_timing_statistics(translated_subtitles)
            logger.info(f"Translation completed for user {user_id}: {timing_stats}")
            
            return final_path
            
        except Exception as e:
            logger.error(f"File processing failed for user {user_id}: {str(e)}")
            # پاکسازی در صورت خطا
            await self.file_manager.cleanup_user_files(user_id, force=True)
            raise Exception(f"پردازش فایل ناموفق: {str(e)}")
    
    async def get_user_preview(self, user_id: int, max_lines: int = 3) -> List[Dict[str, str]]:
        """
        دریافت پیش‌نمایش ترجمه برای کاربر
        
        Args:
            user_id: شناسه کاربر
            max_lines: تعداد خطوط پیش‌نمایش
            
        Returns:
            لیست پیش‌نمایش ترجمه
        """
        try:
            # دریافت مسیر فایل کاربر
            file_path = await self.file_manager.get_user_file_path(user_id)
            if not file_path:
                raise Exception("فایلی برای پیش‌نمایش یافت نشد")
            
            # تجزیه فایل
            subtitles = self.srt_parser.parse_file(file_path)
            if not subtitles:
                return []
            
            # انتخاب زیرنویس‌های اول
            preview_subtitles = subtitles[:max_lines]
            texts_to_translate = [subtitle['text'] for subtitle in preview_subtitles]
            
            # ترجمه پیش‌نمایش
            translated_texts = await self.translator.translate_batch(
                texts_to_translate, 
                settings.TARGET_LANGUAGE
            )
            
            # تولید نتیجه پیش‌نمایش
            preview_result = []
            for i, subtitle in enumerate(preview_subtitles):
                timing_info = subtitle.get('timing_info', {})
                preview_result.append({
                    'index': subtitle.get('index', i + 1),
                    'original': subtitle['text'],
                    'translated': translated_texts[i] if i < len(translated_texts) else subtitle['text'],
                    'timing': subtitle.get('original_timing_line', f"{subtitle.get('start_time', '')} --> {subtitle.get('end_time', '')}"),
                    'duration_ms': timing_info.get('duration_ms', 0)
                })
            
            return preview_result
            
        except Exception as e:
            logger.error(f"Preview generation failed for user {user_id}: {str(e)}")
            raise Exception(f"تولید پیش‌نمایش ناموفق: {str(e)}")
    
    async def cleanup_user_data(self, user_id: int) -> bool:
        """پاکسازی داده‌های کاربر"""
        return await self.file_manager.cleanup_user_files(user_id)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سیستم"""
        file_stats = await self.file_manager.get_system_stats()
        translator_info = self.get_translator_info()
        
        return {
            'file_manager': file_stats,
            'translator': translator_info,
            'settings': {
                'max_file_size_mb': settings.MAX_FILE_SIZE_MB,
                'target_language': settings.TARGET_LANGUAGE,
                'temp_dir': settings.TEMP_DIR,
                'output_dir': settings.OUTPUT_DIR
            }
        }