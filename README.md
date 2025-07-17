 بشه # AI Subtitle Converter 🎬

یک ربات تلگرام برای ترجمه فایل‌های زیرنویس به فارسی با استفاده از هوش مصنوعی

## ویژگی‌ها ✨

### ویژگی‌های اصلی
- 🤖 ترجمه خودکار فایل‌های SRT به فارسی
- 🔄 پشتیبانی از مدل‌های مختلف هوش مصنوعی (شروع با OpenAI)
- 📱 رابط کاربری ساده در تلگرام
- 🔍 پیش‌نمایش ترجمه قبل از دانلود
- ⚙️ قابلیت تغییر آسان مدل ترجمه
- 📊 پشتیبانی از انواع کدگذاری متن

### ویژگی‌های پیشرفته جدید
- 🎯 **حفظ دقیق تایمینگ**: تایمینگ اصلی حفظ شده و فقط متن‌ها ترجمه می‌شوند
- 🗂️ **مدیریت هوشمند فایل**: فضای جداگانه برای هر کاربر
- 🚫 **جلوگیری از تداخل**: یک فایل همزمان برای هر کاربر
- 🧹 **پاکسازی خودکار**: حذف خودکار فایل‌ها بعد از پردازش
- 📏 **کنترل حجم**: محدودیت حجم فایل قابل تنظیم
- 🔒 **امنیت**: عدم تداخل فایل‌های کاربران مختلف
- 📈 **مانیتورینگ**: نظارت بر وضعیت سیستم و کاربران

## نصب و راه‌اندازی 🚀

### پیش‌نیازها
- Python 3.8+
- حساب کاربری Telegram
- کلید API از OpenAI

### مراحل نصب

1. **کلون کردن پروژه:**
```bash
git clone https://github.com/yourusername/AISubConvertor.git
cd AISubConvertor
```

2. **راه‌اندازی خودکار:**
```bash
python setup.py
```

3. **تنظیم متغیرهای محیطی:**
فایل `.env` را ویرایش کنید و کلیدهای API خود ر�� اضافه کنید:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

4. **اجرای ربات:**
```bash
python main.py
```

### راه‌اندازی دستی

اگر راه‌اندازی خودکار کار نکرد:

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# ایجاد پوشه‌های مورد نیاز
mkdir temp output logs

# کپی فایل تنظیمات
cp .env.example .env

# ویرایش فایل .env و اضافه کردن کلیدهای API
# سپس اجرای ربات
python main.py
```

## نحوه استفاده 📖

### دستورات ربات

- `/start` - شروع کار با ربات
- `/help` - راهنمای کامل
- `/info` - اطلاعات مترجم فعلی
- `/preview` - پیش‌نمایش ترجمه

### فرآیند ترجمه

1. فایل SRT خود را به ربات ارسال کنید
2. ربات فایل را دانلود و تجزیه می‌کند
3. متن‌ها به فارسی ترجمه می‌شوند
4. فایل ترجمه شده را دریافت کنید

## ساختار پروژه 🏗️

```
AISubConvertor/
├── src/
│   ├── bot/                    # ربات تلگرام
│   │   ├── telegram_bot.py
│   │   └── __init__.py
│   ├��─ translation/            # سرویس‌های ترجمه
│   │   ├── base.py
│   │   ├── openai_translator.py
│   │   ├── translator_factory.py
│   │   └── __init__.py
│   ├── subtitle/               # پردازش زیرنویس
│   │   ├── srt_parser.py
│   │   └── __init__.py
│   ├── services/               # سرویس‌های اصلی
│   │   ├── translation_service.py
│   │   └── __init__.py
│   └── __init__.py
├── config/                     # تنظیمات
│   ├── settings.py
│   └── __init__.py
├── temp/                       # فایل‌های موقت
├── output/                     # فایل‌های خروجی
├── main.py                     # فایل اصلی
├── setup.py                    # اسکریپت راه‌اندازی
├── requirements.txt            # وابستگی‌ها
├── .env.example               # نمونه تنظیمات
└── README.md
```

## تنظیمات پیشرفته ⚙️

### تغییر مدل ترجمه

برای تغییر مدل OpenAI، فایل `.env` را ویرایش کنید:

```env
OPENAI_MODEL=gpt-4  # یا gpt-3.5-turbo
OPENAI_MAX_TOKENS=4000
```

### ا��افه کردن مترجم جدید

1. کلاس جدید را از `BaseTranslator` ارث‌بری کنید
2. آن را در `TranslatorFactory` ثبت کنید
3. تنظیمات مربوطه را اضافه کنید

مثال:
```python
# src/translation/google_translator.py
class GoogleTranslator(BaseTranslator):
    # پیاده‌سازی مترجم گوگل
    pass

# در translator_factory.py
TranslatorFactory.register_translator('google', GoogleTranslator)
```

## محدودیت‌ها 📋

- حداکثر حجم فایل: 50 مگابایت (قابل تنظیم)
- فرمت‌های پشتیبانی شده: SRT (قابل گسترش)
- زبان مقصد: فارسی
- نیاز به اتصال اینترنت برای ترجمه

## عیب‌یابی 🔧

### مشکلات رایج

1. **خطای "Bot token not found":**
   - بررسی کنید که `TELEGRAM_BOT_TOKEN` در فایل `.env` تنظیم شده باشد

2. **خطای "OpenAI API key not found":**
   - بررسی کنید که `OPENAI_API_KEY` در فایل `.env` تنظیم شده باشد

3. **خطای "Invalid SRT file":**
   - مطمئن شوید فایل شما فرمت SRT صحیح دارد

### لاگ‌ها

لاگ‌های ربات در کنسول نمایش داده می‌شوند. برای تنظیم سطح لاگ:

```env
LOG_LEVEL=DEBUG  # یا INFO, WARNING, ERROR
```

## مشارکت 🤝

برای مشارکت در پروژه:

1. پروژه را Fork کنید
2. شاخه جدید ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات خود را Commit کنید (`git commit -m 'Add amazing feature'`)
4. به شاخه Push کنید (`git push origin feature/amazing-feature`)
5. Pull Request ایجاد کنید

## مجوز 📄

این پروژه تحت مجوز MIT منتشر شده است. فایل [LICENSE](LICENSE) را برای جزئیات بیشتر مطالعه کنید.

## پشتیبانی 💬

- 🐛 گزارش باگ: [Issues](https://github.com/yourusername/AISubConvertor/issues)
- 💡 درخواست ویژگی جدید: [Feature Requests](https://github.com/yourusername/AISubConvertor/issues)
- 📧 تماس مستقیم: your.email@example.com

## تشکر 🙏

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) برای API تلگرام
- [OpenAI](https://openai.com/) برای سرویس‌های ترجمه
- [pysrt](https://github.com/byroot/pysrt) برای پردازش فایل‌های SRT

---

**ساخته شده با ❤️ برای جامعه ایرانی**