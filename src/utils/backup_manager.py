"""
Database Backup Management System
حل مشکل عدم Backup Strategy
"""

import os
import shutil
import sqlite3
import gzip
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger(__name__)

class BackupManager:
    """مدیریت پشتیبان‌گیری پایگاه داده"""
    
    def __init__(self, db_path: str, backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # تنظیمات پشتیبان‌گیری
        self.max_backups = 30  # حداکثر تعداد پشتیبان
        self.compression_enabled = True
        self.verify_backups = True
        
        # شروع پشتیبان‌گیری دوره‌ای
        self._start_periodic_backup()
    
    def create_backup(self, backup_type: str = "manual") -> Optional[str]:
        """ایجاد پشتیبان از پایگاه داده"""
        try:
            if not self.db_path.exists():
                logger.error(f"Database file not found: {self.db_path}")
                return None
            
            # تولید نام فایل پشتیبان
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{timestamp}.db"
            
            if self.compression_enabled:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            # ایجاد پشتیبان
            if self.compression_enabled:
                self._create_compressed_backup(backup_path)
            else:
                self._create_simple_backup(backup_path)
            
            # اعتبارسنجی پشتیبان
            if self.verify_backups and not self._verify_backup(backup_path):
                logger.error(f"Backup verification failed: {backup_path}")
                backup_path.unlink(missing_ok=True)
                return None
            
            # ثبت اطلاعات پشتیبان
            self._record_backup_info(backup_path, backup_type)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return str(backup_path)
        
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _create_simple_backup(self, backup_path: Path):
        """ایجاد پشتیبان ساده"""
        shutil.copy2(self.db_path, backup_path)
    
    def _create_compressed_backup(self, backup_path: Path):
        """ایجاد پشتیبان فشرده"""
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """اعتبارسنجی پشتیبان"""
        try:
            if backup_path.suffix == '.gz':
                # اعتبارسنجی فایل فشرده
                with gzip.open(backup_path, 'rb') as f:
                    # تست خواندن فایل
                    f.read(1024)
                
                # استخراج موقت و تست دیتابیس
                temp_path = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # تست اتصال به دیتابیس
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                # حذف فایل موقت
                temp_path.unlink()
                
                return len(tables) > 0
            
            else:
                # تست دیتابیس غیرفشرده
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                return len(tables) > 0
        
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _record_backup_info(self, backup_path: Path, backup_type: str):
        """ثبت اطلاعات پشتیبان"""
        try:
            info_file = self.backup_dir / "backup_info.json"
            
            # بارگذاری اطلاعات موجود
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
            else:
                backup_info = {"backups": []}
            
            # محاسبه checksum
            checksum = self._calculate_checksum(backup_path)
            
            # اضافه کردن اطلاعات جدید
            backup_record = {
                "filename": backup_path.name,
                "path": str(backup_path),
                "type": backup_type,
                "created_at": datetime.now().isoformat(),
                "size_bytes": backup_path.stat().st_size,
                "checksum": checksum,
                "compressed": backup_path.suffix == '.gz'
            }
            
            backup_info["backups"].append(backup_record)
            
            # ذخیره اطلاعات
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to record backup info: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """محاسبه checksum فایل"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def restore_backup(self, backup_path: str, target_path: str = None) -> bool:
        """بازیابی از پشتیبان"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            target = Path(target_path) if target_path else self.db_path
            
            # ایجاد پشتیبان از فایل فعلی
            if target.exists():
                current_backup = target.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                shutil.copy2(target, current_backup)
                logger.info(f"Current database backed up to: {current_backup}")
            
            # بازیابی
            if backup_file.suffix == '.gz':
                # استخراج فایل فشرده
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(target, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # کپی مستقیم
                shutil.copy2(backup_file, target)
            
            # اعتبارسنجی بازیابی
            if self._verify_restored_database(target):
                logger.info(f"Database restored successfully from: {backup_path}")
                return True
            else:
                logger.error("Restored database verification failed")
                return False
        
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def _verify_restored_database(self, db_path: Path) -> bool:
        """اعتبارسنجی دیتابیس بازیابی شده"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # بررسی جداول اصلی
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            required_tables = ['users', 'subscriptions', 'transactions', 'admins']
            existing_tables = [table[0] for table in tables]
            
            for required_table in required_tables:
                if required_table not in existing_tables:
                    logger.error(f"Required table missing: {required_table}")
                    conn.close()
                    return False
            
            # تست کوئری ساده
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info(f"Database verification passed. Users: {user_count}")
            return True
        
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """لیست پشتیبان‌ها"""
        try:
            info_file = self.backup_dir / "backup_info.json"
            
            if not info_file.exists():
                return []
            
            with open(info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            # مرتب‌سازی بر اساس تاریخ
            backups = backup_info.get("backups", [])
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            return backups
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def cleanup_old_backups(self):
        """پاکسازی پشتیبان‌های قدیمی"""
        try:
            backups = self.list_backups()
            
            if len(backups) <= self.max_backups:
                return
            
            # حذف پشتیبان‌های اضافی
            backups_to_delete = backups[self.max_backups:]
            
            for backup in backups_to_delete:
                backup_path = Path(backup["path"])
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"Deleted old backup: {backup_path}")
            
            # بهروزرسانی فایل اطلاعات
            remaining_backups = backups[:self.max_backups]
            info_file = self.backup_dir / "backup_info.json"
            
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump({"backups": remaining_backups}, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Cleaned up {len(backups_to_delete)} old backups")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def get_backup_stats(self) -> Dict:
        """آمار پشتیبان‌ها"""
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    "total_backups": 0,
                    "total_size_mb": 0,
                    "latest_backup": None,
                    "oldest_backup": None
                }
            
            total_size = sum(backup["size_bytes"] for backup in backups)
            
            return {
                "total_backups": len(backups),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "latest_backup": backups[0]["created_at"],
                "oldest_backup": backups[-1]["created_at"],
                "backup_types": self._get_backup_type_stats(backups)
            }
        
        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return {}
    
    def _get_backup_type_stats(self, backups: List[Dict]) -> Dict:
        """آمار انواع پشتیبان"""
        type_stats = {}
        for backup in backups:
            backup_type = backup["type"]
            type_stats[backup_type] = type_stats.get(backup_type, 0) + 1
        return type_stats
    
    def _start_periodic_backup(self):
        """شروع پشتیبان‌گیری دوره‌ای"""
        async def periodic_backup():
            while True:
                try:
                    # پشتیبان‌گیری هر 24 ساعت
                    await asyncio.sleep(24 * 3600)
                    
                    # ایجاد پشتیبان خودکار
                    backup_path = self.create_backup("automatic")
                    if backup_path:
                        logger.info(f"Automatic backup created: {backup_path}")
                    
                    # پاکسازی پشتیبان‌های قدیمی
                    self.cleanup_old_backups()
                
                except Exception as e:
                    logger.error(f"Periodic backup failed: {e}")
        
        asyncio.create_task(periodic_backup())
    
    def export_data(self, export_path: str) -> bool:
        """صادرات داده‌ها به فرمت JSON"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            export_data = {}
            
            # صادرات جداول
            tables = ['users', 'subscriptions', 'transactions', 'admins', 'system_settings']
            
            for table in tables:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    export_data[table] = [dict(row) for row in rows]
                except sqlite3.OperationalError:
                    # جدول وجود ندارد
                    export_data[table] = []
            
            conn.close()
            
            # ذخیره در فایل JSON
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Data exported to: {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False

# سینگلتون برای استفاده در سراسر برنامه
_backup_manager = None

def get_backup_manager(db_path: str = None) -> BackupManager:
    """دریافت نمونه backup manager"""
    global _backup_manager
    if _backup_manager is None:
        if db_path is None:
            raise ValueError("db_path must be provided for first initialization")
        _backup_manager = BackupManager(db_path)
    return _backup_manager

# مثال استفاده
if __name__ == "__main__":
    # تست backup manager
    backup_mgr = BackupManager("test.db")
    
    # ایجاد پشتیبان
    backup_path = backup_mgr.create_backup("test")
    print(f"Backup created: {backup_path}")
    
    # لیست پشتیبان‌ها
    backups = backup_mgr.list_backups()
    print(f"Available backups: {len(backups)}")
    
    # آمار پشتیبان‌ها
    stats = backup_mgr.get_backup_stats()
    print(f"Backup stats: {stats}")