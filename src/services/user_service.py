import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..database import get_database, UserRole, SubscriptionStatus

logger = logging.getLogger(__name__)

class UserService:
    """سرویس مدیریت کاربران و اشتراک‌ها"""
    
    def __init__(self):
        self.db = get_database()
        self.subscription_plans = {
            'monthly': {
                'name': 'اشتراک ماهانه',
                'duration_days': 30,
                'price': 50000,  # تومان
                'features': ['ترجمه نامحدود', 'پشتیبانی اولویت‌دار', 'کیفیت بالا']
            },
            'yearly': {
                'name': 'اشتراک سالانه',
                'duration_days': 365,
                'price': 500000,  # تومان (تخفیف 17%)
                'features': ['ترجمه نامحدود', 'پشتیبانی اولویت‌دار', 'کیفیت بالا', '17% تخفیف']
            }
        }
    
    async def register_user(self, user_id: int, username: str = None, 
                           first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """ثبت‌نام کاربر جدید"""
        try:
            # بررسی وجود کاربر
            existing_user = self.db.get_user(user_id)
            if existing_user:
                # بهروزرسانی آخرین فعالیت
                self.db.update_user_activity(user_id)
                return {
                    'success': True,
                    'is_new': False,
                    'user': existing_user,
                    'message': 'خوش آمدید! حساب شما قبلاً ایجاد شده است.'
                }
            
            # ایجاد کاربر جدید
            success = self.db.create_user(user_id, username, first_name, last_name)
            if success:
                user = self.db.get_user(user_id)
                return {
                    'success': True,
                    'is_new': True,
                    'user': user,
                    'message': 'حساب شما با موفقیت ایجاد شد! یک ترجمه رایگان در اختیار دارید.'
                }
            else:
                return {
                    'success': False,
                    'message': 'خطا در ایجاد حساب کاربری'
                }
                
        except Exception as e:
            logger.error(f"User registration failed for {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'خطای سیستمی در ثبت‌نام'
            }
    
    async def check_translation_permission(self, user_id: int) -> Dict[str, Any]:
        """بررسی مجوز ترجمه کاربر"""
        try:
            user = self.db.get_user(user_id)
            if not user:
                return {
                    'allowed': False,
                    'reason': 'user_not_found',
                    'message': 'کاربر یافت نشد. لطفاً ابتدا /start را بزنید.'
                }
            
            # بررسی اشتراک فعال
            if user.get('subscription_status') == 'active':
                # بررسی تاریخ انقضا
                end_date = datetime.fromisoformat(user['subscription_end'].replace('Z', '+00:00'))
                if end_date > datetime.now():
                    return {
                        'allowed': True,
                        'type': 'premium',
                        'message': f'اشتراک {user["plan_type"]} فعال است',
                        'remaining_days': (end_date - datetime.now()).days
                    }
            
            # بررسی ترجمه‌های رایگان
            if self.db.can_use_free_translation(user_id):
                remaining = 1 - user.get('free_translations_used', 0)
                return {
                    'allowed': True,
                    'type': 'free',
                    'message': f'شما {remaining} ترجمه رایگان باقی‌مانده دارید',
                    'remaining_free': remaining
                }
            
            # نیاز به خرید اشتراک
            return {
                'allowed': False,
                'reason': 'subscription_required',
                'message': 'ترجمه رایگان شما تمام شده است. برای ادامه، اشتراک تهیه کنید.',
                'plans': self.subscription_plans
            }
            
        except Exception as e:
            logger.error(f"Permission check failed for user {user_id}: {str(e)}")
            return {
                'allowed': False,
                'reason': 'system_error',
                'message': 'خطای سیستمی در بررسی مجوز'
            }
    
    async def use_translation(self, user_id: int, file_name: str, 
                            file_size: int, processing_time: float) -> bool:
        """ثبت استفاده از ترجمه"""
        try:
            user = self.db.get_user(user_id)
            if not user:
                return False
            
            # ثبت تراکنش
            self.db.add_transaction(user_id, file_name, file_size, processing_time, 'completed')
            
            # اگر کاربر رایگان است، شمارنده را افزایش دهیم
            if user.get('subscription_status') != 'active':
                self.db.use_free_translation(user_id)
            
            # بهروزرسانی آخرین فعالیت
            self.db.update_user_activity(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record translation usage for user {user_id}: {str(e)}")
            return False
    
    async def get_subscription_plans(self) -> Dict[str, Any]:
        """دریافت طرح‌های اشتراک"""
        return self.subscription_plans
    
    async def create_subscription(self, user_id: int, plan_type: str) -> Dict[str, Any]:
        """ایجاد اشتراک (شبیه‌سازی پرداخت)"""
        try:
            if plan_type not in self.subscription_plans:
                return {
                    'success': False,
                    'message': 'طرح اشتراک نامعتبر'
                }
            
            plan = self.subscription_plans[plan_type]
            
            # شبیه‌سازی پرداخت موفق
            success = self.db.create_subscription(
                user_id, 
                plan_type, 
                plan['duration_days'], 
                plan['price']
            )
            
            if success:
                return {
                    'success': True,
                    'message': f'اشتراک {plan["name"]} با موفقیت فعال شد!',
                    'plan': plan
                }
            else:
                return {
                    'success': False,
                    'message': 'خطا در فعال‌سازی اشتراک'
                }
                
        except Exception as e:
            logger.error(f"Subscription creation failed for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'خطای سیستمی در ایجاد اشتراک'
            }
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت پروفایل کاربر"""
        try:
            user = self.db.get_user(user_id)
            if not user:
                return None
            
            # محاسبه آمار کاربر
            profile = {
                'user_id': user['user_id'],
                'username': user.get('username'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'role': user['role'],
                'created_at': user['created_at'],
                'total_translations': user['total_translations'],
                'free_translations_used': user['free_translations_used'],
                'subscription': None
            }
            
            # اطلاعات اشتراک
            if user.get('subscription_status') == 'active':
                end_date = datetime.fromisoformat(user['subscription_end'].replace('Z', '+00:00'))
                profile['subscription'] = {
                    'plan_type': user['plan_type'],
                    'status': user['subscription_status'],
                    'end_date': user['subscription_end'],
                    'remaining_days': (end_date - datetime.now()).days
                }
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get user profile {user_id}: {str(e)}")
            return None

class AdminService:
    """سرویس مدیریت ادمین"""
    
    def __init__(self):
        self.db = get_database()
    
    async def is_admin(self, user_id: int) -> bool:
        """بررسی ادمین بودن کاربر"""
        return self.db.is_admin(user_id)
    
    async def add_admin(self, user_id: int, added_by: int) -> Dict[str, Any]:
        """اضافه کردن ادمین جدید"""
        try:
            # بررسی اینکه اضافه‌کننده ادمین است
            if not await self.is_admin(added_by):
                return {
                    'success': False,
                    'message': 'شما مجوز اضافه کردن ادمین ندارید'
                }
            
            success = self.db.add_admin(user_id, added_by)
            if success:
                return {
                    'success': True,
                    'message': f'کاربر {user_id} به عنوان ادمین اضافه شد'
                }
            else:
                return {
                    'success': False,
                    'message': 'خطا در اضافه کردن ادمین'
                }
                
        except Exception as e:
            logger.error(f"Failed to add admin {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'خطای سیستمی'
            }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """دریافت آمار سیستم"""
        return self.db.get_system_stats()
    
    async def get_users_list(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """دریافت لیست کاربران"""
        try:
            offset = (page - 1) * per_page
            users = self.db.get_all_users(per_page, offset)
            
            return {
                'success': True,
                'users': users,
                'page': page,
                'per_page': per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get users list: {str(e)}")
            return {
                'success': False,
                'message': 'خطا در دریافت لیست کاربران'
            }
    
    async def grant_subscription(self, user_id: int, plan_type: str, admin_id: int) -> Dict[str, Any]:
        """اعطای اشتراک رایگان توسط ادمین"""
        try:
            if not await self.is_admin(admin_id):
                return {
                    'success': False,
                    'message': 'شما مجوز اعطای اشتراک ندارید'
                }
            
            user_service = UserService()
            plans = await user_service.get_subscription_plans()
            
            if plan_type not in plans:
                return {
                    'success': False,
                    'message': 'طرح اشتراک نامعتبر'
                }
            
            plan = plans[plan_type]
            success = self.db.create_subscription(
                user_id, plan_type, plan['duration_days'], 0  # قیمت صفر برای اعطای رایگان
            )
            
            if success:
                return {
                    'success': True,
                    'message': f'اشتراک {plan["name"]} به کاربر {user_id} اعطا شد'
                }
            else:
                return {
                    'success': False,
                    'message': 'خطا در اعطای اشتراک'
                }
                
        except Exception as e:
            logger.error(f"Failed to grant subscription: {str(e)}")
            return {
                'success': False,
                'message': 'خطای سیستمی'
            }