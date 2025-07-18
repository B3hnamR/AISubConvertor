import logging
from typing import List, Dict, Any
from ..translation import TranslatorFactory
from ..subtitle import SRTParser, SubtitleTimingManager
from ..utils import (
    get_file_manager, InputValidator, ValidationError,
    handle_errors, TranslationError, FileProcessingError,
    get_error_handler
)
from config import settings, get_dynamic_settings
import os
import asyncio

logger = logging.getLogger(__name__)

class TranslationService:
    """Main service for handling subtitle translation workflow with file management"""
    
    def __init__(self):
        self.srt_parser = SRTParser()
        self.timing_manager = SubtitleTimingManager()
        self.validator = InputValidator()
        self.dynamic_settings = get_dynamic_settings()
        self.error_handler = get_error_handler()
        
        # Initialize file manager with dynamic settings
        max_file_size = self.dynamic_settings.get('file_settings.max_file_size_mb', settings.MAX_FILE_SIZE_MB)
        self.file_manager = get_file_manager(settings.TEMP_DIR, max_file_size)
        
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
    
    @handle_errors(TranslationError, FileProcessingError, reraise=True)
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
            # Input validation
            validated_path = self.validator.validate_file_path(input_file_path)
            validated_max_lines = self.validator.validate_positive_integer(max_lines, "max_lines")
            
            # Parse the SRT file
            subtitles = self.srt_parser.parse_file(validated_path)
            
            if not subtitles:
                return []
            
            # Get first few subtitles for preview
            preview_subtitles = subtitles[:validated_max_lines]
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
            
        except (ValidationError, TranslationError, FileProcessingError) as e:
            self.error_handler.log_error(e, {'method': 'get_translation_preview'})
            raise
        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            self.error_handler.log_error(e, {'method': 'get_translation_preview'})
            raise TranslationError(f"Preview failed: {str(e)}")
    
    def get_translator_info(self) -> Dict[str, Any]:
        """Get information about the current translator"""
        try:
            target_lang = self.dynamic_settings.get('translation_settings.target_language', settings.TARGET_LANGUAGE)
            
            if self.translator:
                return {
                    'provider': self.translator.get_provider_name(),
                    'target_language': target_lang,
                    'available_providers': TranslatorFactory.get_available_providers()
                }
            return {'provider': 'None', 'error': 'Translator not initialized'}
        except Exception as e:
            logger.error(f"Failed to get translator info: {str(e)}")
            return {'error': str(e)}
    
    @handle_errors(ValidationError, TranslationError, reraise=True)
    def change_translator(self, provider: str, config: Dict[str, Any]):
        """Change the translation provider"""
        try:
            validated_provider = self.validator.validate_string(provider, "provider")
            validated_config = self.validator.validate_dict(config, "config")
            
            self.translator = TranslatorFactory.create_translator(validated_provider, validated_config)
            logger.info(f"Changed translator to: {self.translator.get_provider_name()}")
        except (ValidationError, TranslationError) as e:
            self.error_handler.log_error(e, {'method': 'change_translator'})
            raise
        except Exception as e:
            logger.error(f"Failed to change translator: {str(e)}")
            self.error_handler.log_error(e, {'method': 'change_translator'})
            raise TranslationError(f"Translator change failed: {str(e)}")
    
    # متدهای مدیریت فایل
    
    @handle_errors(ValidationError, FileProcessingError, reraise=False)
    async def can_user_upload(self, user_id: int) -> bool:
        """بررسی امکان آپلود فایل برای کاربر"""
        try:
            # Input validation
            validated_user_id = self.validator.validate_user_id(user_id)
            return await self.file_manager.can_upload_file(validated_user_id)
        except ValidationError as e:
            self.error_handler.log_error(e, {'user_id': user_id, 'method': 'can_user_upload'})
            return False
    
    @handle_errors(ValidationError, FileProcessingError, reraise=False)
    async def prepare_file_upload(self, user_id: int, filename: str, file_size: int) -> Dict[str, Any]:
        """آماده‌سازی آپلود فایل"""
        try:
            # Input validation
            validated_user_id = self.validator.validate_user_id(user_id)
            validated_filename = self.validator.validate_filename(filename)
            validated_file_size = self.validator.validate_file_size(file_size)
            
            return await self.file_manager.prepare_user_upload(
                validated_user_id, validated_filename, validated_file_size
            )
        except ValidationError as e:
            self.error_handler.log_error(e, {
                'user_id': user_id, 
                'filename': filename, 
                'file_size': file_size,
                'method': 'prepare_file_upload'
            })
            raise FileProcessingError(f"اعتبارسنجی ناموفق: {str(e)}")
    
    @handle_errors(TranslationError, FileProcessingError, reraise=True)
    async def process_user_file(self, user_id: int, file_path: str) -> str:
        """
        پردازش کام�� فایل کاربر با مدیریت تایمینگ دقیق
        
        Args:
            user_id: شناسه کاربر
            file_path: مسیر فایل دانلود شده
            
        Returns:
            مسیر فایل ترجمه شده
        """
        try:
            # Input validation
            validated_user_id = self.validator.validate_user_id(user_id)
            
            # شروع پردازش
            await self.file_manager.start_file_processing(validated_user_id)
            
            # اعتبارسنجی فایل
            if not self.srt_parser.validate_srt_file(file_path):
                raise FileProcessingError("فرمت فایل SRT نامعتبر است")
            
            # تجزیه فایل با حفظ تایمینگ دقیق
            logger.info(f"Parsing SRT file for user {validated_user_id}: {file_path}")
            original_subtitles = self.srt_parser.parse_file(file_path)
            
            if not original_subtitles:
                raise FileProcessingError("هیچ زیرنویسی در فایل یافت نشد")
            
            # استخراج متن‌ها برای ترجمه
            texts_to_translate = [subtitle['text'] for subtitle in original_subtitles]
            
            # ترجمه متن‌ها
            logger.info(f"Translating {len(texts_to_translate)} subtitle entries for user {validated_user_id}")
            try:
                translated_texts = await self.translator.translate_batch(
                    texts_to_translate, 
                    settings.TARGET_LANGUAGE
                )
            except Exception as e:
                raise TranslationError(f"خطا در ترجمه: {str(e)}")
            
            # حفظ تایمینگ اصلی در ترجمه
            translated_subtitles = self.timing_manager.preserve_timing_in_translation(
                original_subtitles, 
                translated_texts
            )
            
            # تولید مسیر فایل خروجی
            file_info = await self.file_manager.get_user_file_info(validated_user_id)
            if not file_info:
                raise FileProcessingError("اطلاعات فایل کاربر یافت نشد")
            
            base_name = os.path.splitext(file_info['original_filename'])[0]
            output_file_path = os.path.join(
                settings.OUTPUT_DIR,
                f"user_{validated_user_id}",
                f"{base_name}_persian.srt"
            )
            
            # ایجاد دایرکتوری خروجی
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # ذخیره فایل ترجمه شده
            final_path = self.srt_parser.save_srt_file(translated_subtitles, output_file_path)
            
            # تکمیل پردازش
            await self.file_manager.complete_file_processing(validated_user_id, final_path)
            
            # تحلیل آماری نهایی
            timing_stats = self.timing_manager.analyze_timing_statistics(translated_subtitles)
            logger.info(f"Translation completed for user {validated_user_id}: {timing_stats}")
            
            return final_path
            
        except (ValidationError, TranslationError, FileProcessingError) as e:
            self.error_handler.log_error(e, {
                'user_id': user_id, 
                'file_path': file_path,
                'method': 'process_user_file'
            })
            # پاکسازی در صورت خطا
            await self.file_manager.cleanup_user_files(user_id, force=True)
            raise
        except Exception as e:
            logger.error(f"File processing failed for user {user_id}: {str(e)}")
            self.error_handler.log_error(e, {
                'user_id': user_id, 
                'file_path': file_path,
                'method': 'process_user_file'
            })
            # پاکسازی در صورت خطا
            await self.file_manager.cleanup_user_files(user_id, force=True)
            raise FileProcessingError(f"پردازش فایل ناموفق: {str(e)}")
    
    @handle_errors(TranslationError, FileProcessingError, reraise=True)
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
            # Input validation
            validated_user_id = self.validator.validate_user_id(user_id)
            validated_max_lines = self.validator.validate_positive_integer(max_lines, "max_lines")
            
            # دریافت مسیر فایل کاربر
            file_path = await self.file_manager.get_user_file_path(validated_user_id)
            if not file_path:
                logger.warning(f"No file found for preview for user {validated_user_id}")
                return []
            
            # تجزیه فایل
            subtitles = self.srt_parser.parse_file(file_path)
            if not subtitles:
                logger.warning(f"No subtitles found in file for user {validated_user_id}")
                return []
            
            # انتخاب زیرنویس‌های اول
            preview_subtitles = subtitles[:validated_max_lines]
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
            
            logger.info(f"Preview generated successfully for user {validated_user_id}")
            return preview_result
            
        except (ValidationError, TranslationError, FileProcessingError) as e:
            self.error_handler.log_error(e, {'user_id': user_id, 'method': 'get_user_preview'})
            raise
        except Exception as e:
            logger.error(f"Preview generation failed for user {user_id}: {str(e)}")
            self.error_handler.log_error(e, {'user_id': user_id, 'method': 'get_user_preview'})
            raise TranslationError(f"تولید پیش‌نمایش ناموفق: {str(e)}")
    
    @handle_errors(FileProcessingError, reraise=False)
    async def cleanup_user_data(self, user_id: int) -> bool:
        """پاکسازی داده‌های کاربر"""
        try:
            validated_user_id = self.validator.validate_user_id(user_id)
            success = await self.file_manager.cleanup_user_files(validated_user_id)
            logger.info(f"Cleanup {'successful' if success else 'failed'} for user {validated_user_id}")
            return success
        except ValidationError as e:
            self.error_handler.log_error(e, {'user_id': user_id, 'method': 'cleanup_user_data'})
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سیستم"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {'error': str(e)}