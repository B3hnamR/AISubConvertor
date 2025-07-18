import os
import shutil
import asyncio
import hashlib
import time
import weakref
from typing import Dict, Optional, Set
from pathlib import Path
import logging
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class UserFileManager:
    """
    مدیریت فایل‌های کاربران با قابلیت‌های:
    - فضای جداگانه برای هر کاربر
    - پاکسازی خودکار
    - جلوگیری از تداخل
    - محدودیت همزمانی
    - حل مشکل Memory Leak
    """
    
    def __init__(self, base_temp_dir: str, max_file_size_mb: int = 50):
        self.base_temp_dir = Path(base_temp_dir)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # ردیابی فایل‌های فعال هر کاربر
        self.active_files: Dict[int, Dict] = {}  # user_id -> file_info
        self.user_locks: Dict[int, asyncio.Lock] = {}  # user_id -> lock
        self.cleanup_tasks: Dict[int, asyncio.Task] = {}  # user_id -> cleanup_task
        
        # ایجاد دایرکتوری اصلی
        self.base_temp_dir.mkdir(exist_ok=True)
        
        # شروع تسک پاکسازی دوره‌ای
        self._start_periodic_cleanup()
    
    def _get_user_lock(self, user_id: int) -> asyncio.Lock:
        """دریافت یا ایجاد lock برای کاربر"""
        if user_id not in self.user_locks:
            self.user_locks[user_id] = asyncio.Lock()
        return self.user_locks[user_id]
    
    def _get_user_directory(self, user_id: int) -> Path:
        """دریافت دایرکتوری مخصوص کاربر"""
        user_dir = self.base_temp_dir / f"user_{user_id}"
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def _generate_file_id(self, user_id: int, filename: str) -> str:
        """تولید شناسه یکتا برای فایل"""
        timestamp = str(int(time.time()))
        content = f"{user_id}_{filename}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _sanitize_filename(self, filename: str) -> str:
        """ایمن‌سازی نام فایل"""
        if not filename:
            return "unknown.srt"
        
        # حذف کاراکترهای خطرناک
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        safe_filename = "".join(c for c in filename if c in safe_chars)
        
        # اطمینان از وجود پسوند
        if not safe_filename.endswith('.srt'):
            safe_filename += '.srt'
        
        return safe_filename
    
    async def can_upload_file(self, user_id: int) -> bool:
        """بررسی امکان آپلود فایل جدید برای کاربر"""
        if not isinstance(user_id, int) or user_id <= 0:
            return False
            
        async with self._get_user_lock(user_id):
            # بررسی وجود فایل فعال
            if user_id in self.active_files:
                active_file = self.active_files[user_id]
                # بررسی اینکه فایل هنوز در حال پردازش است
                if active_file.get('status') in ['downloading', 'processing']:
                    return False
            return True
    
    async def validate_file_size(self, file_size: int) -> bool:
        """اعتبارسنجی حجم فایل"""
        return isinstance(file_size, int) and 0 < file_size <= self.max_file_size_bytes
    
    async def prepare_user_upload(self, user_id: int, filename: str, file_size: int) -> Optional[Dict]:
        """آماده‌سازی برای آپلود فایل کاربر"""
        # Input validation
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user_id")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Invalid filename")
        if not isinstance(file_size, int) or file_size <= 0:
            raise ValueError("Invalid file_size")
        
        async with self._get_user_lock(user_id):
            try:
                # بررسی امکان آپلود
                if not await self.can_upload_file(user_id):
                    raise Exception("کاربر در حال حاضر فایل دیگری در حال پردازش دارد")
                
                # بررسی حجم فایل
                if not await self.validate_file_size(file_size):
                    raise Exception(f"حجم فایل بیش از حد مجاز است. حداکثر: {self.max_file_size_bytes // (1024*1024)} مگابایت")
                
                # پاکسازی فایل‌های قبلی کاربر
                await self._cleanup_user_files(user_id)
                
                # تولید اطلاعات فایل جدید
                file_id = self._generate_file_id(user_id, filename)
                user_dir = self._get_user_directory(user_id)
                
                # تولید نام فایل امن
                safe_filename = self._sanitize_filename(filename)
                file_path = user_dir / f"{file_id}_{safe_filename}"
                
                file_info = {
                    'file_id': file_id,
                    'original_filename': filename,
                    'file_path': str(file_path),
                    'file_size': file_size,
                    'status': 'preparing',
                    'created_at': datetime.now(),
                    'user_id': user_id
                }
                
                # ثبت فایل فعال
                self.active_files[user_id] = file_info
                
                logger.info(f"Prepared upload for user {user_id}: {filename} ({file_size} bytes)")
                return file_info
                
            except Exception as e:
                logger.error(f"Failed to prepare upload for user {user_id}: {str(e)}")
                raise
    
    async def start_file_download(self, user_id: int) -> bool:
        """شروع دانلود فایل"""
        async with self._get_user_lock(user_id):
            if user_id in self.active_files:
                self.active_files[user_id]['status'] = 'downloading'
                self.active_files[user_id]['download_started_at'] = datetime.now()
                return True
            return False
    
    async def complete_file_download(self, user_id: int) -> bool:
        """تکمیل دانلود فایل"""
        async with self._get_user_lock(user_id):
            if user_id in self.active_files:
                file_info = self.active_files[user_id]
                file_path = Path(file_info['file_path'])
                
                # بررسی وجود فایل
                if not file_path.exists():
                    raise Exception("فایل دانلود نشده است")
                
                # بررسی حجم فایل دانلود شده
                actual_size = file_path.stat().st_size
                expected_size = file_info['file_size']
                
                if actual_size != expected_size:
                    logger.warning(f"File size mismatch for user {user_id}: expected {expected_size}, got {actual_size}")
                
                self.active_files[user_id]['status'] = 'downloaded'
                self.active_files[user_id]['download_completed_at'] = datetime.now()
                self.active_files[user_id]['actual_size'] = actual_size
                
                logger.info(f"Download completed for user {user_id}: {file_info['original_filename']}")
                return True
            return False
    
    async def start_file_processing(self, user_id: int) -> bool:
        """شروع پردازش فایل"""
        async with self._get_user_lock(user_id):
            if user_id in self.active_files and self.active_files[user_id]['status'] == 'downloaded':
                self.active_files[user_id]['status'] = 'processing'
                self.active_files[user_id]['processing_started_at'] = datetime.now()
                
                # تنظیم تسک پاکسازی خودکار (30 دقیقه)
                self._schedule_cleanup(user_id, delay_minutes=30)
                return True
            return False
    
    async def complete_file_processing(self, user_id: int, output_file_path: str) -> bool:
        """تکمیل پردازش فایل"""
        async with self._get_user_lock(user_id):
            if user_id in self.active_files:
                self.active_files[user_id]['status'] = 'completed'
                self.active_files[user_id]['processing_completed_at'] = datetime.now()
                self.active_files[user_id]['output_file_path'] = output_file_path
                
                # تنظیم پاکسازی سریع‌تر (5 دقیقه)
                self._schedule_cleanup(user_id, delay_minutes=5)
                
                logger.info(f"Processing completed for user {user_id}")
                return True
            return False
    
    async def get_user_file_info(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات فایل فعال کاربر"""
        async with self._get_user_lock(user_id):
            return self.active_files.get(user_id)
    
    async def get_user_file_path(self, user_id: int) -> Optional[str]:
        """دریافت مسیر فایل کاربر"""
        file_info = await self.get_user_file_info(user_id)
        if file_info and file_info['status'] in ['downloaded', 'processing', 'completed']:
            return file_info['file_path']
        return None
    
    async def cleanup_user_files(self, user_id: int, force: bool = False) -> bool:
        """پاکسازی فایل‌های کاربر"""
        async with self._get_user_lock(user_id):
            return await self._cleanup_user_files(user_id, force)
    
    async def _cleanup_user_files(self, user_id: int, force: bool = False) -> bool:
        """پاکسازی داخلی فایل‌های کاربر"""
        try:
            # لغو تسک پاکسازی قبلی
            if user_id in self.cleanup_tasks:
                self.cleanup_tasks[user_id].cancel()
                del self.cleanup_tasks[user_id]
            
            # بررسی وضعیت فایل
            if user_id in self.active_files:
                file_info = self.active_files[user_id]
                
                # اگر فایل در حال پردازش است و force نیست، پاکسازی نکن
                if not force and file_info['status'] in ['downloading', 'processing']:
                    logger.info(f"Skipping cleanup for user {user_id}: file is being processed")
                    return False
                
                # پاک کردن فایل‌های ورودی و خروجی
                input_path = Path(file_info['file_path'])
                if input_path.exists():
                    input_path.unlink()
                    logger.info(f"Deleted input file: {input_path}")
                
                output_path = file_info.get('output_file_path')
                if output_path and Path(output_path).exists():
                    Path(output_path).unlink()
                    logger.info(f"Deleted output file: {output_path}")
                
                # حذف از فایل‌های فعال
                del self.active_files[user_id]
            
            # پاک کردن دایرکتوری کاربر اگر خالی است
            user_dir = self._get_user_directory(user_id)
            if user_dir.exists() and not any(user_dir.iterdir()):
                user_dir.rmdir()
                logger.info(f"Deleted empty user directory: {user_dir}")
            
            # پاکسازی memory leak: حذف lock و task اگر کاربر دیگر فعال نیست
            self._cleanup_user_resources(user_id)
            
            logger.info(f"Cleanup completed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Cleanup failed for user {user_id}: {str(e)}")
            return False
    
    def _cleanup_user_resources(self, user_id: int):
        """پاکسازی منابع حافظه برای کاربر غیرفعال"""
        try:
            # اگر کاربر فایل فعال ندارد، lock و task را پاک کن
            if user_id not in self.active_files:
                # پاک کردن lock
                if user_id in self.user_locks:
                    del self.user_locks[user_id]
                    logger.debug(f"Cleaned up lock for user {user_id}")
                
                # پاک کردن cleanup task
                if user_id in self.cleanup_tasks:
                    if not self.cleanup_tasks[user_id].done():
                        self.cleanup_tasks[user_id].cancel()
                    del self.cleanup_tasks[user_id]
                    logger.debug(f"Cleaned up task for user {user_id}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup resources for user {user_id}: {str(e)}")
    
    def _schedule_cleanup(self, user_id: int, delay_minutes: int = 5):
        """برنامه‌ریزی پاکسازی خودکار"""
        async def delayed_cleanup():
            try:
                await asyncio.sleep(delay_minutes * 60)
                await self.cleanup_user_files(user_id)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Scheduled cleanup failed for user {user_id}: {str(e)}")
        
        # لغو تسک قبلی
        if user_id in self.cleanup_tasks:
            self.cleanup_tasks[user_id].cancel()
        
        # ایجاد تسک جدید
        self.cleanup_tasks[user_id] = asyncio.create_task(delayed_cleanup())
    
    def _start_periodic_cleanup(self):
        """شروع پاکسازی دوره‌ای"""
        async def periodic_cleanup():
            while True:
                try:
                    await asyncio.sleep(3600)  # هر ساعت
                    await self._cleanup_old_files()
                    await self._cleanup_orphaned_resources()
                except Exception as e:
                    logger.error(f"Periodic cleanup failed: {str(e)}")
        
        asyncio.create_task(periodic_cleanup())
    
    async def _cleanup_old_files(self):
        """پاکسازی فایل‌های قدیمی"""
        cutoff_time = datetime.now() - timedelta(hours=2)
        users_to_cleanup = []
        
        for user_id, file_info in self.active_files.items():
            if file_info['created_at'] < cutoff_time:
                users_to_cleanup.append(user_id)
        
        for user_id in users_to_cleanup:
            await self.cleanup_user_files(user_id, force=True)
            logger.info(f"Force cleaned up old files for user {user_id}")
    
    async def _cleanup_orphaned_resources(self):
        """پاکسازی منابع یتیم (locks و tasks بدون فایل فعال)"""
        try:
            # پیدا کردن locks یتیم
            orphaned_locks = []
            for user_id in list(self.user_locks.keys()):
                if user_id not in self.active_files:
                    orphaned_locks.append(user_id)
            
            # پاک کردن locks یتیم
            for user_id in orphaned_locks:
                del self.user_locks[user_id]
                logger.debug(f"Cleaned up orphaned lock for user {user_id}")
            
            # پیدا کردن tasks یتیم
            orphaned_tasks = []
            for user_id in list(self.cleanup_tasks.keys()):
                if user_id not in self.active_files:
                    orphaned_tasks.append(user_id)
            
            # پاک کردن tasks یتیم
            for user_id in orphaned_tasks:
                if not self.cleanup_tasks[user_id].done():
                    self.cleanup_tasks[user_id].cancel()
                del self.cleanup_tasks[user_id]
                logger.debug(f"Cleaned up orphaned task for user {user_id}")
            
            if orphaned_locks or orphaned_tasks:
                logger.info(f"Cleaned up {len(orphaned_locks)} orphaned locks and {len(orphaned_tasks)} orphaned tasks")
        
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned resources: {str(e)}")
    
    async def get_system_stats(self) -> Dict:
        """دریافت آمار سیستم"""
        total_active_files = len(self.active_files)
        total_size = 0
        status_counts = {}
        
        for file_info in self.active_files.values():
            total_size += file_info.get('actual_size', file_info['file_size'])
            status = file_info['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'active_files': total_active_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'status_breakdown': status_counts,
            'base_directory': str(self.base_temp_dir),
            'memory_usage': {
                'active_locks': len(self.user_locks),
                'active_tasks': len(self.cleanup_tasks)
            }
        }

# سینگلتون برای استفاده در سراسر برنامه
_file_manager_instance = None

def get_file_manager(base_temp_dir: str = None, max_file_size_mb: int = 50) -> UserFileManager:
    """دریافت نمونه مدیریت فایل (Singleton)"""
    global _file_manager_instance
    if _file_manager_instance is None:
        if base_temp_dir is None:
            raise ValueError("base_temp_dir must be provided for first initialization")
        _file_manager_instance = UserFileManager(base_temp_dir, max_file_size_mb)
    return _file_manager_instance