"""
Input Validation Utilities
حل مشکل عدم Validation ورودی‌ها
"""

import re
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """خطای اعتبارسنجی"""
    pass

class InputValidator:
    """کلاس اعتبارسنجی ورودی‌ها"""
    
    @staticmethod
    def validate_user_id(user_id: Any) -> int:
        """اعتبارسنجی شناسه کاربر"""
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                raise ValidationError("شناسه کاربر باید عدد صحیح باشد")
        
        if user_id <= 0:
            raise ValidationError("شناسه کاربر باید مثبت باشد")
        
        if user_id > 2**63 - 1:  # Max int64
            raise ValidationError("شناسه کاربر خیلی بزرگ است")
        
        return user_id
    
    @staticmethod
    def validate_filename(filename: Any) -> str:
        """اعتبارسنجی نام فایل"""
        if not isinstance(filename, str):
            raise ValidationError("نام فایل باید رشته باشد")
        
        filename = filename.strip()
        if not filename:
            raise ValidationError("نام فایل نمی‌تواند خالی باشد")
        
        if len(filename) > 255:
            raise ValidationError("نام فایل خیلی طولانی است")
        
        # کاراکترهای غیرمجاز در نام فایل
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in forbidden_chars:
            if char in filename:
                raise ValidationError(f"نام فایل نمی‌تواند شامل کاراکتر '{char}' باشد")
        
        # بررسی Path Traversal
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            raise ValidationError("نام فایل نامعتبر است")
        
        return filename
    
    @staticmethod
    def validate_file_size(file_size: Any, max_size_mb: int = 50) -> int:
        """اعتبارسنجی حجم فایل"""
        if not isinstance(file_size, int):
            try:
                file_size = int(file_size)
            except (ValueError, TypeError):
                raise ValidationError("حجم فایل باید عدد صحیح باشد")
        
        if file_size <= 0:
            raise ValidationError("حجم فایل باید مثبت باشد")
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValidationError(f"حجم فایل نباید بیش از {max_size_mb} مگابایت باشد")
        
        return file_size
    
    @staticmethod
    def validate_plan_type(plan_type: Any) -> str:
        """اعتبارسنجی نوع طرح اشتراک"""
        if not isinstance(plan_type, str):
            raise ValidationError("نوع طرح باید رشته باشد")
        
        plan_type = plan_type.strip().lower()
        valid_plans = ['monthly', 'yearly']
        
        if plan_type not in valid_plans:
            raise ValidationError(f"نوع طرح باید یکی از {valid_plans} باشد")
        
        return plan_type
    
    @staticmethod
    def validate_text_input(text: Any, max_length: int = 1000, allow_empty: bool = False) -> str:
        """اعتبارسنجی ورودی متنی"""
        if not isinstance(text, str):
            raise ValidationError("ورودی باید رشته باشد")
        
        text = text.strip()
        
        if not allow_empty and not text:
            raise ValidationError("ورودی نمی‌تواند خالی باشد")
        
        if len(text) > max_length:
            raise ValidationError(f"طول ورودی نباید بیش از {max_length} کاراکتر باشد")
        
        # بررسی کاراکترهای مشکوک
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError("ورودی شامل محتوای مشکوک است")
        
        return text
    
    @staticmethod
    def validate_file_path(file_path: Any, base_dir: Optional[str] = None) -> str:
        """اعتبارسنجی مسیر فایل"""
        if not isinstance(file_path, str):
            raise ValidationError("مسیر فایل باید رشته باشد")
        
        file_path = file_path.strip()
        if not file_path:
            raise ValidationError("مسیر فایل نمی‌تواند خالی باشد")
        
        # تبدیل به Path object
        try:
            path_obj = Path(file_path)
        except Exception:
            raise ValidationError("مسیر فایل نامعتبر است")
        
        # بررسی Path Traversal
        if '..' in path_obj.parts:
            raise ValidationError("مسیر فایل نمی‌تواند شامل '..' باشد")
        
        # بررسی مسیر مطلق
        if path_obj.is_absolute() and base_dir:
            base_path = Path(base_dir).resolve()
            try:
                path_obj.resolve().relative_to(base_path)
            except ValueError:
                raise ValidationError("مسیر فایل خارج از دایرکتوری مجاز است")
        
        return str(path_obj)
    
    @staticmethod
    def validate_email(email: Any) -> str:
        """اعتبارسنجی ایمیل"""
        if not isinstance(email, str):
            raise ValidationError("ایمیل باید رشته باشد")
        
        email = email.strip().lower()
        
        # الگوی ساده ایمیل
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("فرمت ایمیل نامعتبر است")
        
        if len(email) > 254:  # RFC 5321
            raise ValidationError("ایمیل خیلی طولانی است")
        
        return email
    
    @staticmethod
    def validate_json_data(data: Any, max_size: int = 10000) -> Dict:
        """اعتبارسنجی داده JSON"""
        if not isinstance(data, dict):
            raise ValidationError("داده باید dictionary باشد")
        
        # بررسی حجم JSON
        import json
        json_str = json.dumps(data)
        if len(json_str) > max_size:
            raise ValidationError(f"حجم داده JSON نباید بیش از {max_size} کاراکتر باشد")
        
        return data
    
    @staticmethod
    def sanitize_sql_input(input_str: str) -> str:
        """پاکسازی ورودی برای جلوگیری از SQL Injection"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # حذف کاراکترهای خطرناک
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = input_str
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_pagination(page: Any, per_page: Any, max_per_page: int = 100) -> tuple[int, int]:
        """اعتبارسنجی پارامترهای صفحه‌بندی"""
        # اعتبارسنجی شماره صفحه
        if not isinstance(page, int):
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1
        
        if page < 1:
            page = 1
        
        # اعتبارسنجی تعداد آیتم در صفحه
        if not isinstance(per_page, int):
            try:
                per_page = int(per_page)
            except (ValueError, TypeError):
                per_page = 20
        
        if per_page < 1:
            per_page = 20
        elif per_page > max_per_page:
            per_page = max_per_page
        
        return page, per_page

def validate_input(validator_func, *args, **kwargs):
    """دکوریتور برای اعتبارسنجی ورودی‌ها"""
    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            try:
                # اعتبارسنجی ورودی‌ها
                validated_args = []
                for i, arg in enumerate(func_args):
                    if i < len(args):
                        validated_args.append(validator_func(arg))
                    else:
                        validated_args.append(arg)
                
                return func(*validated_args, **func_kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error in {func.__name__}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

# مثال استفاده
if __name__ == "__main__":
    validator = InputValidator()
    
    # تست اعتبارسنجی
    try:
        user_id = validator.validate_user_id("123")
        print(f"Valid user_id: {user_id}")
        
        filename = validator.validate_filename("test.srt")
        print(f"Valid filename: {filename}")
        
        file_size = validator.validate_file_size(1024000)
        print(f"Valid file_size: {file_size}")
        
    except ValidationError as e:
        print(f"Validation error: {e}")