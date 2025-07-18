#!/usr/bin/env python3
"""
Test script for premium system (users, subscriptions, admin)
"""

import sys
import os
import asyncio
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database import DatabaseManager, get_database
from src.services import UserService, AdminService

async def test_database():
    """Test database functionality"""
    print("🧪 Testing Database System...")
    print("=" * 50)
    
    # ایجاد دیتابیس موقت
    temp_db = tempfile.mktemp(suffix='.db')
    
    try:
        db = DatabaseManager(temp_db)
        
        # تست ایجاد کاربر
        user_id = 123456789
        success = db.create_user(user_id, "testuser", "Test", "User")
        print(f"✅ User creation: {success}")
        
        # تست دریافت کاربر
        user = db.get_user(user_id)
        print(f"✅ User retrieval: {user is not None}")
        print(f"   User data: {user['first_name']} {user['last_name']}")
        
        # تست بررسی ترجمه رایگان
        can_use = db.can_use_free_translation(user_id)
        print(f"✅ Can use free translation: {can_use}")
        
        # تست استفاده از ترجمه رایگان
        db.use_free_translation(user_id)
        can_use_after = db.can_use_free_translation(user_id)
        print(f"✅ Can use free translation after use: {can_use_after}")
        
        # تست ایجاد اشتراک
        subscription_success = db.create_subscription(user_id, "monthly", 30, 50000)
        print(f"✅ Subscription creation: {subscription_success}")
        
        # تست اضافه کردن ادمین
        admin_success = db.add_admin(user_id, user_id)
        print(f"✅ Admin addition: {admin_success}")
        
        # تست بررسی ادمین
        is_admin = db.is_admin(user_id)
        print(f"✅ Admin check: {is_admin}")
        
        # تست آمار سیستم
        stats = db.get_system_stats()
        print(f"✅ System stats: {stats}")
        
        print(f"\n🎉 Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False
        
    finally:
        # پاکسازی
        try:
            os.remove(temp_db)
        except:
            pass

async def test_user_service():
    """Test user service functionality"""
    print("\n🧪 Testing User Service...")
    print("=" * 50)
    
    try:
        user_service = UserService()
        
        # تست ثبت‌نام کاربر
        user_id = 987654321
        result = await user_service.register_user(user_id, "newuser", "New", "User")
        print(f"✅ User registration: {result['success']}")
        print(f"   Is new user: {result['is_new']}")
        
        # تست بررسی مجوز ترجمه
        permission = await user_service.check_translation_permission(user_id)
        print(f"✅ Translation permission: {permission['allowed']}")
        print(f"   Permission type: {permission.get('type', 'unknown')}")
        
        # تست استفاده از ترجمه
        usage_success = await user_service.use_translation(
            user_id, "test.srt", 1024, 5.5
        )
        print(f"✅ Translation usage: {usage_success}")
        
        # تست بررسی مجوز بعد از استفاده
        permission_after = await user_service.check_translation_permission(user_id)
        print(f"✅ Permission after use: {permission_after['allowed']}")
        print(f"   Reason: {permission_after.get('reason', 'allowed')}")
        
        # تست دریافت طرح‌های اشتراک
        plans = await user_service.get_subscription_plans()
        print(f"✅ Subscription plans: {len(plans)} plans available")
        
        # تست ایجاد اشتراک
        subscription_result = await user_service.create_subscription(user_id, "monthly")
        print(f"✅ Subscription creation: {subscription_result['success']}")
        
        # تست پروفایل کاربر
        profile = await user_service.get_user_profile(user_id)
        print(f"✅ User profile: {profile is not None}")
        if profile:
            print(f"   Role: {profile['role']}")
            print(f"   Total translations: {profile['total_translations']}")
        
        print(f"\n🎉 User Service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ User Service test failed: {str(e)}")
        return False

async def test_admin_service():
    """Test admin service functionality"""
    print("\n🧪 Testing Admin Service...")
    print("=" * 50)
    
    try:
        admin_service = AdminService()
        
        # تست کاربر ادمین
        admin_id = 111111111
        user_id = 222222222
        
        # ابتدا ادمین را اضافه کنیم
        db = get_database()
        db.create_user(admin_id, "admin", "Admin", "User")
        db.add_admin(admin_id, admin_id)
        
        # تست بررسی ادمین
        is_admin = await admin_service.is_admin(admin_id)
        print(f"✅ Admin check: {is_admin}")
        
        # تست اضافه کردن ادمین جدید
        db.create_user(user_id, "newadmin", "New", "Admin")
        add_result = await admin_service.add_admin(user_id, admin_id)
        print(f"✅ Add new admin: {add_result['success']}")
        
        # تست دریافت آمار سیستم
        stats = await admin_service.get_system_stats()
        print(f"✅ System stats: {stats}")
        
        # تست دریافت لیست کاربران
        users_result = await admin_service.get_users_list()
        print(f"✅ Users list: {users_result['success']}")
        print(f"   Users count: {len(users_result.get('users', []))}")
        
        # تست اعطای اشتراک
        grant_result = await admin_service.grant_subscription(user_id, "yearly", admin_id)
        print(f"✅ Grant subscription: {grant_result['success']}")
        
        print(f"\n🎉 Admin Service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Admin Service test failed: {str(e)}")
        return False

async def test_subscription_flow():
    """Test complete subscription flow"""
    print("\n🧪 Testing Subscription Flow...")
    print("=" * 50)
    
    try:
        user_service = UserService()
        
        # کاربر جدید
        user_id = 333333333
        
        # ثبت‌نام
        await user_service.register_user(user_id, "flowuser", "Flow", "User")
        
        # بررسی مجوز اولیه (باید 1 ترجمه رایگان داشته باشد)
        permission1 = await user_service.check_translation_permission(user_id)
        print(f"✅ Initial permission: {permission1['allowed']} ({permission1.get('type')})")
        
        # استفاده از ترجمه رایگان
        await user_service.use_translation(user_id, "test1.srt", 1024, 3.0)
        
        # بررسی مجوز بعد از استفاده (نباید مجوز داشته باشد)
        permission2 = await user_service.check_translation_permission(user_id)
        print(f"✅ Permission after free use: {permission2['allowed']}")
        print(f"   Reason: {permission2.get('reason')}")
        
        # خرید اشتراک
        subscription_result = await user_service.create_subscription(user_id, "monthly")
        print(f"✅ Subscription purchase: {subscription_result['success']}")
        
        # بررسی مجوز بعد از خرید اشتراک (باید مجوز داشته باشد)
        permission3 = await user_service.check_translation_permission(user_id)
        print(f"✅ Permission after subscription: {permission3['allowed']} ({permission3.get('type')})")
        
        # استفاده از ترجمه با اشتراک
        await user_service.use_translation(user_id, "test2.srt", 2048, 4.5)
        
        # بررسی مجوز بعد از استفاده با اشتراک (باید همچنان مجوز داشته باشد)
        permission4 = await user_service.check_translation_permission(user_id)
        print(f"✅ Permission after premium use: {permission4['allowed']} ({permission4.get('type')})")
        
        # بررسی پروفایل نهایی
        profile = await user_service.get_user_profile(user_id)
        print(f"✅ Final profile:")
        print(f"   Role: {profile['role']}")
        print(f"   Total translations: {profile['total_translations']}")
        print(f"   Free translations used: {profile['free_translations_used']}")
        print(f"   Has subscription: {profile['subscription'] is not None}")
        
        print(f"\n🎉 Subscription Flow test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Subscription Flow test failed: {str(e)}")
        return False

async def main():
    """Run all premium system tests"""
    print("🚀 Starting Premium System Tests...")
    print("=" * 60)
    
    # تست دیتابیس
    db_test_success = await test_database()
    
    # تست سرویس کاربران
    user_test_success = await test_user_service()
    
    # تست سرویس ادمین
    admin_test_success = await test_admin_service()
    
    # تست جریان اشتراک
    flow_test_success = await test_subscription_flow()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"   Database: {'✅ PASSED' if db_test_success else '❌ FAILED'}")
    print(f"   User Service: {'✅ PASSED' if user_test_success else '❌ FAILED'}")
    print(f"   Admin Service: {'✅ PASSED' if admin_test_success else '❌ FAILED'}")
    print(f"   Subscription Flow: {'✅ PASSED' if flow_test_success else '❌ FAILED'}")
    
    all_passed = all([db_test_success, user_test_success, admin_test_success, flow_test_success])
    
    if all_passed:
        print("\n🎉 All premium system tests passed! Ready for production.")
        print("\n💡 Next steps:")
        print("1. Set SUPER_ADMIN_IDS in .env file")
        print("2. Configure payment gateway (if needed)")
        print("3. Deploy and test with real users")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)