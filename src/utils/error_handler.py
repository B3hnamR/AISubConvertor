"""
Advanced Error Handling System
حل مشکل Error Handling ناکافی
"""

import logging
import traceback
import functools
from typing import Any, Callable, Dict, Optional, Type, Union
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class AISubConvertorError(Exception):
    """کلاس پایه خطاهای سیستم"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class DatabaseError(AISubConvertorError):
    """خطاهای پایگاه داده"""
    pass

class TranslationError(AISubConvertorError):
    """خطاهای ترجمه"""
    pass

class FileProcessingError(AISubConvertorError):
    """خطاهای پردازش فایل"""
    pass

class ValidationError(AISubConvertorError):
    """خطاهای اعتبارسنجی"""
    pass

class AuthenticationError(AISubConvertorError):
    """خطاهای احراز هویت"""
    pass

class PermissionError(AISubConvertorError):
    """خطاهای مجوز"""
    pass

class RateLimitError(AISubConvertorError):
    """خطاهای محدودیت نرخ"""
    pass

class ExternalServiceError(AISubConvertorError):
    """خطاهای سرویس‌های خارجی"""
    pass

class ErrorHandler:
    """مدیریت پیشرفته خطاها"""
    
    def __init__(self):
        self.error_stats = {}
        self.error_callbacks = {}
    
    def register_callback(self, error_type: Type[Exception], callback: Callable):
        """ثبت callback برای نوع خطای خاص"""
        self.error_callbacks[error_type] = callback
    
    def log_error(self, error: Exception, context: Dict = None):
        """ثبت دقیق خطا"""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        # آمار خطاها
        error_type = type(error).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        # لاگ بر اساس نوع خطا
        if isinstance(error, (DatabaseError, TranslationError, FileProcessingError)):
            logger.error(f"Critical error: {error_info}")
        elif isinstance(error, (ValidationError, AuthenticationError, PermissionError)):
            logger.warning(f"User error: {error_info}")
        elif isinstance(error, RateLimitError):
            logger.info(f"Rate limit error: {error_info}")
        else:
            logger.error(f"Unexpected error: {error_info}")
        
        # اجرای callback اگر وجود دارد
        if type(error) in self.error_callbacks:
            try:
                self.error_callbacks[type(error)](error, context)
            except Exception as callback_error:
                logger.error(f"Error in callback: {callback_error}")
    
    def get_user_friendly_message(self, error: Exception) -> str:
        """تولید پیام کاربرپسند برای خطا"""
        if isinstance(error, DatabaseError):
            return "خطای موقت در سیستم. لطفاً دوباره تلاش کنید."
        
        elif isinstance(error, TranslationError):
            return "خطا در ترجمه. لطفاً فایل خود را بررسی کنید."
        
        elif isinstance(error, FileProcessingError):
            return "خطا در پردازش فایل. فرمت فایل را بررسی کنید."
        
        elif isinstance(error, ValidationError):
            return f"ورودی نامعتبر: {error.message}"
        
        elif isinstance(error, AuthenticationError):
            return "خطا در احراز هویت. لطفاً دوباره وارد شوید."
        
        elif isinstance(error, PermissionError):
            return "شما مجوز انجام این عمل را ندارید."
        
        elif isinstance(error, RateLimitError):
            return "تعداد درخواست‌های شما زیاد است. لطفاً کمی صبر کنید."
        
        elif isinstance(error, ExternalServiceError):
            return "خطا در سرویس خارجی. لطفاً بعداً تلاش کنید."
        
        else:
            return "خطای غیرمنتظره. لطفاً با پشتیبانی تماس بگیرید."
    
    def get_error_stats(self) -> Dict:
        """دریافت آمار خطاها"""
        return self.error_stats.copy()

# نمونه سینگلتون
_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """دریافت نمونه error handler"""
    return _error_handler

def handle_errors(
    error_types: Union[Type[Exception], tuple] = Exception,
    reraise: bool = True,
    default_return: Any = None,
    log_context: Dict = None
):
    """دکوریتور مدیریت خطا"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # محدود کردن طول
                    'kwargs': str(kwargs)[:200],
                    **(log_context or {})
                }
                
                _error_handler.log_error(e, context)
                
                if reraise:
                    raise
                return default_return
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200],
                    **(log_context or {})
                }
                
                _error_handler.log_error(e, context)
                
                if reraise:
                    raise
                return default_return
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """اجرای ایمن تابع"""
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        _error_handler.log_error(e, {
            'function': func.__name__,
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        })
        return False, None

async def safe_execute_async(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """اجرای ایمن تابع async"""
    try:
        result = await func(*args, **kwargs)
        return True, result
    except Exception as e:
        _error_handler.log_error(e, {
            'function': func.__name__,
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        })
        return False, None

class DatabaseErrorHandler:
    """مدیریت خطاهای پایگاه داده"""
    
    @staticmethod
    def handle_sqlite_error(error: Exception) -> DatabaseError:
        """تبدیل خطاهای SQLite به خطاهای سیستم"""
        error_msg = str(error).lower()
        
        if 'database is locked' in error_msg:
            return DatabaseError(
                "پایگاه داده قفل است",
                "DB_LOCKED",
                {'original_error': str(error)}
            )
        
        elif 'no such table' in error_msg:
            return DatabaseError(
                "جدول پایگاه داده یافت نشد",
                "TABLE_NOT_FOUND",
                {'original_error': str(error)}
            )
        
        elif 'constraint failed' in error_msg:
            return DatabaseError(
                "نقض محدودیت پایگاه داده",
                "CONSTRAINT_VIOLATION",
                {'original_error': str(error)}
            )
        
        elif 'disk i/o error' in error_msg:
            return DatabaseError(
                "خطای دیسک",
                "DISK_ERROR",
                {'original_error': str(error)}
            )
        
        else:
            return DatabaseError(
                "خطای پایگاه داده",
                "DB_GENERAL_ERROR",
                {'original_error': str(error)}
            )

class TranslationErrorHandler:
    """مدیریت خطاهای ترجمه"""
    
    @staticmethod
    def handle_openai_error(error: Exception) -> TranslationError:
        """تبدیل خطاهای OpenAI به خطاهای سیستم"""
        error_msg = str(error).lower()
        
        if 'rate limit' in error_msg:
            return RateLimitError(
                "محدودیت نرخ OpenAI",
                "OPENAI_RATE_LIMIT",
                {'original_error': str(error)}
            )
        
        elif 'invalid api key' in error_msg:
            return ExternalServiceError(
                "کلید API نامعتبر",
                "INVALID_API_KEY",
                {'original_error': str(error)}
            )
        
        elif 'quota exceeded' in error_msg:
            return ExternalServiceError(
                "سهمیه OpenAI تمام شده",
                "QUOTA_EXCEEDED",
                {'original_error': str(error)}
            )
        
        elif 'timeout' in error_msg:
            return ExternalServiceError(
                "تایم‌اوت سرویس ترجمه",
                "TRANSLATION_TIMEOUT",
                {'original_error': str(error)}
            )
        
        else:
            return TranslationError(
                "خطای ترجمه",
                "TRANSLATION_ERROR",
                {'original_error': str(error)}
            )

# مثال استفاده
if __name__ == "__main__":
    # تست error handler
    @handle_errors(DatabaseError, reraise=False, default_return=None)
    def test_function():
        raise DatabaseError("Test database error", "TEST_ERROR")
    
    result = test_function()
    print(f"Result: {result}")
    
    # آمار خطاها
    stats = get_error_handler().get_error_stats()
    print(f"Error stats: {stats}")