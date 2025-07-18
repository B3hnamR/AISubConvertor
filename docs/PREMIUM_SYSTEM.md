# سیستم پریمیوم AI Subtitle Converter 💎

این مستند سیستم کامل اشتراک، مدیریت کاربران و پنل ادمین را شرح می‌دهد.

## 🏗️ معماری سیستم

### اجزای اصلی:
- **DatabaseManager**: مدیریت پایگاه داده SQLite
- **UserService**: سرویس مدیریت کاربران و اشتراک‌ها
- **AdminService**: سرویس مدیریت ادمین‌ها
- **TelegramBotPremium**: ربات تلگرام با قابلیت‌های پریمیوم

### ساختار دیتابیس:
```sql
-- کاربران
users (user_id, username, first_name, last_name, role, created_at, 
       last_activity, is_active, free_translations_used, total_translations, settings)

-- اشتراک‌ها
subscriptions (id, user_id, plan_type, status, start_date, end_date, 
               price, payment_method, created_at)

-- تراکنش‌ها
transactions (id, user_id, file_name, file_size, processing_time, 
              status, created_at)

-- ادمین‌ها
admins (user_id, permissions, added_by, added_at)

-- تنظیمات سیستم
system_settings (key, value, updated_at)
```

## 👥 سیستم کاربران

### نقش‌های کاربری:
- **🆓 Free**: کاربر رایگان (1 ترجمه)
- **💎 Premium**: کاربر پریمیوم (ترجمه نامحدود)
- **👑 Admin**: مدیر سیستم

### فرآیند ثبت‌نام:
1. کاربر `/start` می‌زند
2. سیستم کاربر را ثبت می‌کند
3. 1 ترجمه رایگان اعطا می‌شود
4. کاربر می‌تواند فایل ارسال کند

### مدیریت ترجمه‌های رایگان:
```python
# بررسی مجوز ترجمه
permission = await user_service.check_translation_permission(user_id)

if permission['allowed']:
    if permission['type'] == 'free':
        # ترجمه رایگان
        remaining = permission['remaining_free']
    elif permission['type'] == 'premium':
        # ترجمه نامحدود
        pass
else:
    # نیاز به خرید اشتراک
    reason = permission['reason']
```

## 💳 سیستم اشتراک

### طرح‌های اشتراک:

#### 📅 ماهانه:
- **قیمت**: 50,000 تومان
- **مدت**: 30 روز
- **ویژگی‌ها**: ترجمه نامحدود، پشتیبانی اولویت‌دار

#### 📆 سالانه:
- **قیمت**: 500,000 تومان (17% تخفیف)
- **مدت**: 365 روز
- **ویژگی‌ها**: همه ویژگی‌های ماهانه + تخفیف

### فرآیند خرید:
1. کاربر `/subscribe` می‌زند
2. طرح‌های موجود نمایش داده می‌شود
3. کاربر طرح مورد نظر را انتخاب می‌کند
4. پرداخت انجام می‌شود (شبیه‌سازی شده)
5. اشتراک فعال می‌شود

### کد نمونه:
```python
# خرید اشتراک
result = await user_service.create_subscription(user_id, "monthly")

if result['success']:
    # اشتراک فعال شد
    message = result['message']
else:
    # خطا در خرید
    error = result['message']
```

## 👑 سیستم مدیریت

### سطوح دسترسی:
- **Super Admin**: ادمین‌های اولیه (از .env)
- **Admin**: ادمین‌های اضافه شده

### دستورات ادمین:

#### `/admin` - پنل مدیریت
نمایش دستورات موجود برای ادمین

#### `/stats` - آمار سیستم
```
📊 آمار سیستم
کاربران:
• کل: 1,250
• پریمیوم: 320
• رایگان: 930

تراکنش‌ها:
• کل: 5,680
• هفته گذشته: 245

درآمد:
• کل: 16,000,000 تومان
```

#### `/users` - لیست کاربران
نمایش 10 کاربر اخیر با نقش‌هایشان

#### `/addadmin [user_id]` - اضافه کردن ادمین
```bash
/addadmin 123456789
```

#### `/grant [user_id] [plan]` - اعطای اشتراک رایگان
```bash
/grant 123456789 monthly
/grant 987654321 yearly
```

### کد نمونه ادمین:
```python
# بررسی ادمین بودن
if await admin_service.is_admin(user_id):
    # دسترسی به عملیات ادمین
    stats = await admin_service.get_system_stats()
    users = await admin_service.get_users_list()
```

## 🔧 تنظیمات سیستم

### فایل .env:
```env
# ادمین‌های اولیه (کاما جدا)
SUPER_ADMIN_IDS=123456789,987654321

# محدودیت ترجمه رایگان
FREE_TRANSLATIONS_LIMIT=1

# مسیر دیتابیس
DATABASE_PATH=./aisubconvertor.db
```

### تنظیمات طرح‌های اشتراک:
```python
subscription_plans = {
    'monthly': {
        'name': 'اشتراک ماهانه',
        'duration_days': 30,
        'price': 50000,
        'features': ['ترجمه نامحدود', 'پشتیبانی اولویت‌دار']
    },
    'yearly': {
        'name': 'اشتراک سالانه', 
        'duration_days': 365,
        'price': 500000,
        'features': ['ترجمه نامحدود', 'پشتیبانی ا��لویت‌دار', '17% تخفیف']
    }
}
```

## 🚀 راه‌اندازی

### 1. تنظیم ادمین‌ها:
```env
# در فایل .env
SUPER_ADMIN_IDS=YOUR_USER_ID,ANOTHER_ADMIN_ID
```

### 2. اجرای ربات:
```bash
python main.py
```

### 3. تست سیستم:
```bash
python tests/test_premium_system.py
```

## 📱 تجربه کاربری

### کاربر جدید:
1. `/start` → ثبت‌نام + 1 ترجمه رایگان
2. ارسال فایل → ترجمه موفق
3. ارسال فایل دوم → پیام نیاز به اشتراک
4. `/subscribe` → خرید اشتراک
5. ارسال فایل → ترجمه نامحدود

### کاربر پریمیوم:
1. ارسال فایل → ترجمه فوری
2. `/profile` → مشاهده وضعیت اشتراک
3. دریافت اطلاعات باقی‌مانده روزهای اشتراک

### ادمین:
1. `/admin` → دسترسی به پنل مدیریت
2. `/stats` → مشاهده آمار کامل
3. `/grant user_id monthly` → اعطای اشتراک رایگان
4. `/addadmin user_id` → اضافه کردن ادمین جدید

## 🔒 امنیت

### محافظت از دیتابیس:
- استفاده از SQLite با تراکنش‌های ایمن
- Prepared statements برای جلوگیری از SQL Injection
- رمزگذاری اطلاعات حساس (در نسخه‌های آینده)

### کنترل دسترسی:
- بررسی مجوز در هر درخواست
- جداسازی کامل کاربران
- لاگ تمام عملیات مهم

### محدودیت‌ها:
- یک فایل همزمان برای هر کاربر
- محدودیت حجم فایل
- Rate limiting (در نسخه‌های آینده)

## 📊 مانیتورینگ

### لاگ‌های مهم:
```
INFO - User 123456789 registered successfully
INFO - Subscription created for user 123456789: monthly
INFO - Translation completed for user 123456789: 5.2s
WARNING - User 987654321 exceeded free limit
ERROR - Payment failed for user 555555555
```

### آمار قابل ردیابی:
- تعداد کاربران جدید روزانه
- نرخ تبدیل از رایگان به پریمیوم
- میانگین زمان پردازش
- درآمد روزانه/ماهانه

## 🔮 ویژگی‌های آینده

### پرداخت واقعی:
- اتصال به درگاه‌های پرداخت ایرانی
- پشتیبانی از کارت‌های بانکی
- کیف پول داخلی

### ویژگی‌های پیشرفته:
- کد تخفیف
- برنامه ارجاع دوستان
- اشتراک گروهی
- API برای توسعه‌دهندگان

### بهبودهای عملکرد:
- کش Redis
- Queue system
- Load balancing
- CDN برای فایل‌ها

---

**این سیستم آماده تولید و قابل مقیاس‌گذاری است.**