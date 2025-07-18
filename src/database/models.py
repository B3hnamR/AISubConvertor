import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """نقش‌های کاربری"""
    ADMIN = "admin"
    PREMIUM = "premium"
    FREE = "free"

class SubscriptionStatus(Enum):
    """وضعیت اشتراک"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

class DatabaseManager:
    """مدیریت پایگاه داده SQLite با Thread Safety"""
    
    def __init__(self, db_path: str = "aisubconvertor.db"):
        self.db_path = db_path
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._local = threading.local()  # Thread-local storage for connections
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """دریافت connection thread-safe با context manager"""
        with self._lock:
            try:
                # استفاده از connection pool ساده
                if not hasattr(self._local, 'connection'):
                    self._local.connection = sqlite3.connect(
                        self.db_path,
                        timeout=30.0,  # 30 second timeout
                        check_same_thread=False
                    )
                    # تنظیمات بهینه‌سازی
                    self._local.connection.execute("PRAGMA journal_mode=WAL")
                    self._local.connection.execute("PRAGMA synchronous=NORMAL")
                    self._local.connection.execute("PRAGMA cache_size=10000")
                    self._local.connection.execute("PRAGMA temp_store=memory")
                
                yield self._local.connection
                
            except Exception as e:
                # در صورت خطا، connection را ببند
                if hasattr(self._local, 'connection'):
                    try:
                        self._local.connection.close()
                    except:
                        pass
                    delattr(self._local, 'connection')
                raise e
    
    def close_connection(self):
        """بستن connection thread فعلی"""
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
            except:
                pass
            delattr(self._local, 'connection')
    
    def init_database(self):
        """ایجاد جداول پایگاه داده"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # جدول کاربران
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        role TEXT DEFAULT 'free',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        free_translations_used INTEGER DEFAULT 0,
                        total_translations INTEGER DEFAULT 0,
                        settings TEXT DEFAULT '{}'
                    )
                """)
                
                # جدول اشتراک‌ها
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        plan_type TEXT,
                        status TEXT DEFAULT 'pending',
                        start_date TIMESTAMP,
                        end_date TIMESTAMP,
                        price REAL,
                        payment_method TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # جدول تراکنش‌ها
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        file_name TEXT,
                        file_size INTEGER,
                        processing_time REAL,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # جدول تنظیمات سیستم
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # جدول ادمین‌ها
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        user_id INTEGER PRIMARY KEY,
                        permissions TEXT DEFAULT '{}',
                        added_by INTEGER,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id: {user_id}")
            return None
            
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT u.*, s.plan_type, s.status as subscription_status, 
                           s.end_date as subscription_end
                    FROM users u
                    LEFT JOIN subscriptions s ON u.user_id = s.user_id 
                        AND s.status = 'active'
                    WHERE u.user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    try:
                        user_data['settings'] = json.loads(user_data.get('settings', '{}'))
                    except json.JSONDecodeError:
                        user_data['settings'] = {}
                    return user_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            return None
    
    def create_user(self, user_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> bool:
        """ایجاد کاربر جدید"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO users 
                    (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, first_name, last_name))
                
                conn.commit()
                logger.info(f"User {user_id} created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {str(e)}")
            return False
    
    def update_user_activity(self, user_id: int) -> bool:
        """بهروزرسانی آخرین فعالیت کاربر"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to update activity for user {user_id}: {str(e)}")
            return False
    
    def use_free_translation(self, user_id: int) -> bool:
        """استفاده از ترجمه رایگان"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET free_translations_used = free_translations_used + 1,
                        total_translations = total_translations + 1
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to use free translation for user {user_id}: {str(e)}")
            return False
    
    def can_use_free_translation(self, user_id: int, max_free: int = 1) -> bool:
        """بررسی امکان استفاده از ترجمه رایگان"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # اگر اشتراک فعال دارد
        if user.get('subscription_status') == 'active':
            return True
        
        # بررسی ترجمه‌های رایگان
        return user.get('free_translations_used', 0) < max_free
    
    def create_subscription(self, user_id: int, plan_type: str, 
                          duration_days: int, price: float) -> bool:
        """ایجاد اشتراک جدید"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = datetime.now()
                end_date = start_date + timedelta(days=duration_days)
                
                cursor.execute("""
                    INSERT INTO subscriptions 
                    (user_id, plan_type, status, start_date, end_date, price)
                    VALUES (?, ?, 'active', ?, ?, ?)
                """, (user_id, plan_type, start_date, end_date, price))
                
                # بهروزرسانی نقش کاربر
                cursor.execute("""
                    UPDATE users SET role = 'premium' WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"Subscription created for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create subscription for user {user_id}: {str(e)}")
            return False
    
    def add_transaction(self, user_id: int, file_name: str, 
                       file_size: int, processing_time: float, status: str) -> bool:
        """ثبت تراکنش"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO transactions 
                    (user_id, file_name, file_size, processing_time, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, file_name, file_size, processing_time, status))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add transaction: {str(e)}")
            return False
    
    def is_admin(self, user_id: int) -> bool:
        """بررسی ادمین بودن کاربر"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 1 FROM admins WHERE user_id = ?
                """, (user_id,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Failed to check admin status for user {user_id}: {str(e)}")
            return False
    
    def add_admin(self, user_id: int, added_by: int, permissions: Dict = None) -> bool:
        """اضافه کردن ادمین"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                permissions_json = json.dumps(permissions or {})
                
                cursor.execute("""
                    INSERT OR REPLACE INTO admins 
                    (user_id, permissions, added_by)
                    VALUES (?, ?, ?)
                """, (user_id, permissions_json, added_by))
                
                # بهروزرسانی نقش کاربر
                cursor.execute("""
                    UPDATE users SET role = 'admin' WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"Admin {user_id} added by {added_by}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add admin {user_id}: {str(e)}")
            return False
    
    def get_system_stats(self) -> Dict:
        """دریافت آمار سیستم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # آمار کاربران
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'premium'")
                premium_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'free'")
                free_users = cursor.fetchone()[0]
                
                # آمار تراکنش‌ها
                cursor.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM transactions 
                    WHERE created_at >= date('now', '-7 days')
                """)
                weekly_transactions = cursor.fetchone()[0]
                
                # آمار درآمد
                cursor.execute("SELECT SUM(price) FROM subscriptions WHERE status = 'active'")
                total_revenue = cursor.fetchone()[0] or 0
                
                return {
                    'users': {
                        'total': total_users,
                        'premium': premium_users,
                        'free': free_users
                    },
                    'transactions': {
                        'total': total_transactions,
                        'weekly': weekly_transactions
                    },
                    'revenue': {
                        'total': total_revenue
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get system stats: {str(e)}")
            return {}
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """دریافت لیست کاربران"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT u.*, s.plan_type, s.status as subscription_status
                    FROM users u
                    LEFT JOIN subscriptions s ON u.user_id = s.user_id 
                        AND s.status = 'active'
                    ORDER BY u.created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get users list: {str(e)}")
            return []

# سینگلتون برای استفاده در سراسر برنامه
_db_instance = None

def get_database() -> DatabaseManager:
    """دریافت نمونه پایگاه داده (Singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance