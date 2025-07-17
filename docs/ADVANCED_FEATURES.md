# ویژگی‌های پیشرفته AI Subtitle Converter 🚀

این مستند ویژگی‌های پیشرفته سیستم ترجمه زیرنویس را شرح می‌دهد.

## 🗂️ مدیریت هوشمند فایل

### ویژگی‌ها:
- **فضای جداگانه**: هر کاربر فضای اختصاصی دارد
- **جلوگیری از تداخل**: یک فایل همزمان برای هر کاربر
- **پاکسازی خودکار**: حذف فایل‌ها بعد از پردازش
- **کنترل حجم**: محدودیت حجم قابل تنظیم

### نحوه کارکرد:

```python
# مثال استفاده از مدیر فایل
from src.utils import get_file_manager

file_manager = get_file_manager("./temp", max_file_size_mb=50)

# بررسی امکان آپلود
can_upload = await file_manager.can_upload_file(user_id)

# آماده‌سازی آپلود
file_info = await file_manager.prepare_user_upload(
    user_id, filename, file_size
)

# پاکسازی
await file_manager.cleanup_user_files(user_id)
```

### ساختار دایرکتوری:
```
temp/
├── user_12345/
│   └── abc123_movie.srt
├── user_67890/
│   └── def456_series.srt
└── ...

output/
├── user_12345/
│   └── movie_persian.srt
├── user_67890/
│   └── series_persian.srt
└── ...
```

## 🎯 مدیریت دقیق تایمینگ

### ویژگی‌ها:
- **حفظ کامل تایمینگ**: زمان‌بندی اصلی دست نخورده باقی می‌ماند
- **اعتبارسنجی**: بررسی صحت تایمینگ
- **آمار تحلیلی**: تحلیل آماری زیرنویس‌ها
- **تشخیص خطا**: شناسایی مشکلات تایمینگ

### مثال کد:

```python
from src.subtitle import SubtitleTimingManager

timing_manager = SubtitleTimingManager()

# تجزیه تایمینگ
timing_info = timing_manager.parse_timing_line(
    "00:01:23,456 --> 00:01:27,890"
)

# حفظ تایمینگ در ترجمه
translated_subtitles = timing_manager.preserve_timing_in_translation(
    original_subtitles, translated_texts
)

# آمار تایمینگ
stats = timing_manager.analyze_timing_statistics(subtitles)
```

### فرمت تایمینگ:
```
ساعت:دقیقه:ثانیه,میلی‌ثانیه --> ساعت:دقیقه:ثانیه,میلی‌ثانیه
00:01:23,456 --> 00:01:27,890
```

## 🔒 امنیت و جداسازی

### اصول امنیتی:
1. **جداسازی کاربران**: فایل‌های هر کاربر در فضای جداگانه
2. **محدودیت همزمانی**: جلوگیری از آپلود همزمان
3. **پاکسازی خودکار**: حذف فایل‌ها بعد از مدت زمان مشخص
4. **اعتبارسنجی**: بررسی نوع و حجم فایل

### تنظیمات امنیتی:

```env
# حداکثر حجم فایل (مگابایت)
MAX_FILE_SIZE_MB=50

# زمان پاکسازی خودکار (دقیقه)
AUTO_CLEANUP_MINUTES=5

# حداکثر فایل‌های همزمان
MAX_CONCURRENT_FILES=1
```

## 📊 مانیتورینگ و آمار

### آمار سیستم:
- تعداد فایل‌های فعال
- حجم کل استفاده شده
- وضعیت هر فایل
- آمار کاربران

### دستورات مانیتورینگ:

```bash
# مشاهده وضعیت سیستم
/status

# پاکسازی دستی
/cleanup

# اطلاعات مترجم
/info
```

### مثال خروجی آمار:

```json
{
  "file_manager": {
    "active_files": 3,
    "total_size_mb": 2.5,
    "status_breakdown": {
      "processing": 2,
      "completed": 1
    }
  },
  "translator": {
    "provider": "OpenAI (gpt-3.5-turbo)",
    "target_language": "Persian"
  }
}
```

## 🔄 چرخه حیات فایل

### مراحل پردازش:

1. **آماده‌سازی** (`preparing`)
   - بررسی امکان آپلود
   - ایجاد فضای کاربر
   - تولید شناسه فایل

2. **دانلود** (`downloading`)
   - دریافت فایل از تلگرام
   - ذخیره در فضای کاربر
   - اعتبارسنجی حجم

3. **پردازش** (`processing`)
   - تجزیه فایل SRT
   - ترجمه متن‌ها
   - حفظ تایمینگ

4. **تکمیل** (`completed`)
   - ایجاد فایل خروجی
   - آماده برای دانلود
   - برنامه‌ریزی پاکسازی

5. **پاکسازی** (`cleanup`)
   - حذف فایل‌های ورودی و خروجی
   - آزادسازی فضا

### نمودار جریان:

```
آپلود فایل → بررسی امکان → آماده‌سازی → دانلود → پردازش → تکمیل → پاکسازی
     ↓              ↓            ↓         ↓        ↓        ↓         ↓
  اعتبارسنجی   جداسازی کاربر   ایجاد فضا   ذخیره   ترجمه   خروجی   حذف فایل‌ها
```

## ⚙️ تنظیمات پیشرفته

### فایل تنظیمات (.env):

```env
# تنظیمات فایل
MAX_FILE_SIZE_MB=50
TEMP_DIR=./temp
OUTPUT_DIR=./output

# تنظیمات پاکسازی
AUTO_CLEANUP_MINUTES=5
PERIODIC_CLEANUP_HOURS=1

# تنظیمات همزمانی
MAX_CONCURRENT_REQUESTS=5
USER_RATE_LIMIT=1

# تنظیمات لاگ
LOG_LEVEL=INFO
```

### تنظیمات مترجم:

```env
# OpenAI
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=4000

# زبان
TARGET_LANGUAGE=Persian
SOURCE_LANGUAGE=auto-detect
```

## 🧪 تست و عیب‌یابی

### اجرای تست‌ها:

```bash
# تست مدیریت فایل
python tests/test_file_management.py

# تست پارسر SRT
python tests/test_srt_parser.py

# تست ترجمه
python tests/test_translation.py
```

### عیب‌یابی رایج:

1. **فایل پاک نمی‌شود**:
   - بررسی مجوزهای دایرکتوری
   - اجرای `/cleanup` دستی

2. **خطای حجم فایل**:
   - بررسی تنظیم `MAX_FILE_SIZE_MB`
   - کاهش حجم فایل

3. **تداخل کاربران**:
   - بررسی لاگ‌ها
   - اجرای `/status` برای مشاهده وضعیت

### لاگ‌های مفید:

```
INFO - Parsed 150 subtitle entries with precise timing
INFO - Translation completed for user 12345: {'total_subtitles': 150, 'duration': '01:45:30,000'}
INFO - Cleanup completed for user 12345
```

## 🔮 ویژگی‌های آینده

### در دست توسعه:
- پشتیبانی از فرمت‌های بیشتر (VTT, ASS)
- ترجمه به زبان‌های مختلف
- کش ترجمه برای بهبود سرعت
- API RESTful برای توسعه‌دهندگان

### پیشنهادات بهبود:
- استفاده از Redis برای کش
- پیاده‌سازی Queue system
- اضافه کردن Database
- ایجاد Dashboard مدیریت

---

**این مستند به صورت مداوم بهروزرسانی می‌شود.**