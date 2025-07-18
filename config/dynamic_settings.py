"""
Dynamic Settings Management
حل مشکل Hard-coded Values
"""

import os
import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class DynamicSettings:
    """مدیریت تنظیمات پویا"""
    
    def __init__(self, config_file: str = "dynamic_config.json"):
        self.config_file = Path(config_file)
        self.settings = {}
        self.default_settings = self._get_default_settings()
        self.load_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """تنظیمات پیش‌فرض سیستم"""
        return {
            # تنظیمات اشتراک
            "subscription_plans": {
                "monthly": {
                    "name": "اشتراک ماهانه",
                    "duration_days": 30,
                    "price": 50000,
                    "currency": "IRR",
                    "features": [
                        "ترجمه نامحدود",
                        "پشتیبانی اولویت‌دار",
                        "کیفیت بالا"
                    ],
                    "max_file_size_mb": 50,
                    "max_concurrent_files": 3
                },
                "yearly": {
                    "name": "اشتراک سالانه",
                    "duration_days": 365,
                    "price": 500000,
                    "currency": "IRR",
                    "discount_percent": 17,
                    "features": [
                        "ترجمه نامحدود",
                        "پشتیبانی اولویت‌دار",
                        "کیفیت بالا",
                        "17% تخفیف"
                    ],
                    "max_file_size_mb": 100,
                    "max_concurrent_files": 5
                }
            },
            
            # تنظیمات رایگان
            "free_plan": {
                "translations_limit": 1,
                "max_file_size_mb": 25,
                "max_concurrent_files": 1,
                "features": [
                    "تست سرویس",
                    "کیفیت استاندارد"
                ]
            },
            
            # تنظیمات فایل
            "file_settings": {
                "max_file_size_mb": 50,
                "allowed_extensions": [".srt"],
                "cleanup_delay_minutes": 5,
                "max_processing_time_minutes": 30,
                "temp_file_retention_hours": 2
            },
            
            # تنظیمات ترجمه
            "translation_settings": {
                "default_model": "gpt-3.5-turbo",
                "max_tokens": 4000,
                "temperature": 0.3,
                "batch_size": 10,
                "retry_attempts": 3,
                "timeout_seconds": 60
            },
            
            # تنظیمات امنیتی
            "security_settings": {
                "rate_limit_per_minute": 10,
                "rate_limit_per_hour": 100,
                "max_login_attempts": 5,
                "session_timeout_minutes": 60,
                "password_min_length": 8
            },
            
            # تنظیمات لاگ
            "logging_settings": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            
            # تنظیمات پایگاه داده
            "database_settings": {
                "backup_interval_hours": 24,
                "max_connections": 10,
                "connection_timeout_seconds": 30,
                "query_timeout_seconds": 60
            },
            
            # تنظیمات کش
            "cache_settings": {
                "enabled": True,
                "ttl_seconds": 3600,
                "max_size_mb": 100,
                "cleanup_interval_minutes": 30
            },
            
            # پیام‌های سیستم
            "system_messages": {
                "welcome_message": "🎉 خوش آمدید به سرویس ترجمه زیرنویس پریمیوم!",
                "subscription_expired": "⏰ اشتراک شما منقضی شده است. برای تمدید اقدام کنید.",
                "file_too_large": "📁 حجم فایل بیش از حد مجاز است.",
                "processing_error": "❌ خطا در پردازش فایل. لطفاً دوباره تلاش کنید.",
                "maintenance_mode": "🔧 سیستم در حال تعمیر است. لطفاً بعداً تلاش کنید."
            },
            
            # تنظیمات نوتیفیکیشن
            "notification_settings": {
                "email_enabled": False,
                "sms_enabled": False,
                "telegram_enabled": True,
                "admin_notifications": True
            },
            
            # تنظیمات عملکرد
            "performance_settings": {
                "max_concurrent_users": 100,
                "max_queue_size": 1000,
                "worker_threads": 4,
                "memory_limit_mb": 512
            }
        }
    
    def load_settings(self):
        """بارگذاری تنظیمات از فایل"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                
                # ترکیب با تنظیمات پیش‌فرض
                self.settings = self._merge_settings(self.default_settings, file_settings)
                logger.info(f"Settings loaded from {self.config_file}")
            else:
                self.settings = self.default_settings.copy()
                self.save_settings()
                logger.info("Default settings created")
        
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        """ذخیره تنظیمات در فایل"""
        try:
            # ایجاد دایرکتوری اگر وجود ندارد
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Settings saved to {self.config_file}")
        
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def _merge_settings(self, default: Dict, custom: Dict) -> Dict:
        """ترکیب تنظیمات پیش‌فرض با سفارشی"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """دریافت تنظیم با کلید"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = True):
        """تنظیم مقدار با کلید"""
        keys = key.split('.')
        current = self.settings
        
        # پیمایش تا آخرین کلید
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # تنظیم مقدار
        current[keys[-1]] = value
        
        if save:
            self.save_settings()
        
        logger.info(f"Setting updated: {key} = {value}")
    
    def get_subscription_plan(self, plan_type: str) -> Optional[Dict]:
        """دریافت اطلاعات طرح اشتراک"""
        return self.get(f"subscription_plans.{plan_type}")
    
    def get_all_subscription_plans(self) -> Dict:
        """دریافت تمام طرح‌های اشتراک"""
        return self.get("subscription_plans", {})
    
    def update_subscription_plan(self, plan_type: str, updates: Dict):
        """بهروزرسانی طرح اشتراک"""
        current_plan = self.get_subscription_plan(plan_type)
        if current_plan:
            current_plan.update(updates)
            self.set(f"subscription_plans.{plan_type}", current_plan)
    
    def get_system_message(self, message_key: str) -> str:
        """دریافت پیام سیستم"""
        return self.get(f"system_messages.{message_key}", "پیام یافت نشد")
    
    def update_system_message(self, message_key: str, message: str):
        """بهروزرسانی پیام سیستم"""
        self.set(f"system_messages.{message_key}", message)
    
    def get_file_settings(self) -> Dict:
        """دریافت تنظیمات فایل"""
        return self.get("file_settings", {})
    
    def get_translation_settings(self) -> Dict:
        """دریافت تنظیمات ترجمه"""
        return self.get("translation_settings", {})
    
    def get_security_settings(self) -> Dict:
        """دریافت تنظیمات امنیتی"""
        return self.get("security_settings", {})
    
    def is_maintenance_mode(self) -> bool:
        """بررسی حالت تعمیر"""
        return self.get("maintenance_mode", False)
    
    def set_maintenance_mode(self, enabled: bool):
        """تنظیم حالت تعمیر"""
        self.set("maintenance_mode", enabled)
    
    def get_feature_flags(self) -> Dict:
        """دریافت فلگ‌های ویژگی"""
        return self.get("feature_flags", {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """بررسی فعال بودن ویژگی"""
        return self.get(f"feature_flags.{feature_name}", False)
    
    def enable_feature(self, feature_name: str):
        """فعال کردن ویژگی"""
        self.set(f"feature_flags.{feature_name}", True)
    
    def disable_feature(self, feature_name: str):
        """غیرفعال کردن ویژگی"""
        self.set(f"feature_flags.{feature_name}", False)
    
    def reset_to_defaults(self):
        """بازگشت به تنظیمات پیش‌فرض"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        logger.info("Settings reset to defaults")
    
    def export_settings(self, file_path: str):
        """صادرات تنظیمات"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info(f"Settings exported to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
    
    def import_settings(self, file_path: str):
        """وارد کرد�� تنظیمات"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            self.settings = self._merge_settings(self.default_settings, imported_settings)
            self.save_settings()
            logger.info(f"Settings imported from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
    
    def get_settings_summary(self) -> Dict:
        """خلاصه تنظیمات"""
        return {
            "total_plans": len(self.get_all_subscription_plans()),
            "maintenance_mode": self.is_maintenance_mode(),
            "max_file_size": self.get("file_settings.max_file_size_mb"),
            "free_translations": self.get("free_plan.translations_limit"),
            "last_updated": datetime.now().isoformat()
        }

# سینگلتون برای استفاده در سراسر برنامه
_dynamic_settings = None

def get_dynamic_settings() -> DynamicSettings:
    """دریافت نمونه تنظیمات پویا"""
    global _dynamic_settings
    if _dynamic_settings is None:
        _dynamic_settings = DynamicSettings()
    return _dynamic_settings

# مثال استفاده
if __name__ == "__main__":
    settings = get_dynamic_settings()
    
    # تست دریافت تنظیمات
    monthly_plan = settings.get_subscription_plan("monthly")
    print(f"Monthly plan: {monthly_plan}")
    
    # تست تغییر تنظیمات
    settings.set("subscription_plans.monthly.price", 55000)
    
    # تست پیام‌های سیستم
    welcome_msg = settings.get_system_message("welcome_message")
    print(f"Welcome message: {welcome_msg}")
    
    # خلاصه تنظیمات
    summary = settings.get_settings_summary()
    print(f"Settings summary: {summary}")