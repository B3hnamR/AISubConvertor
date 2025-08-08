# AISubConvertor — Project Assessment and Completion Plan

این سند شامل ارزیابی وضعیت فعلی پروژه، مشکلات شناسایی‌شده، و نقشه راه مرحله‌به‌مرحله برای تکمیل و پایدارسازی است.

---

## 1) وضعیت فعلی پروژه

- ترجمه و زیرنویس
  - Translation layer: `src/translation/` با `BaseTranslator`, `TranslatorFactory`, و `OpenAITranslator` پیاده‌سازی شده است.
  - زیرنویس: `SRTParser` و `SubtitleTimingManager` با مدیریت دقیق تایمینگ و اعتبارسنجی/آمار زمان‌بندی.
- سرویس‌ها
  - `TranslationService`: جریان کامل پردازش فایل SRT به ترجمه فارسی، مدیریت فایل، و پیش‌نمایش.
  - `UserService` و `AdminService`: ثبت‌نام، اشتراک‌ها، پروفایل، و عملیات ادمین.
- زیرساخت
  - مدیریت فایل کاربران: `UserFileManager` با قفل‌گذاری، محدودیت حجم، پاکسازی زمان‌بندی‌شده، و جلوگیری از Memory Leak.
  - تنظیمات: `config/settings.py` و `config/dynamic_settings.py` کامل و یکپارچه هستند.
  - مدیریت خطا و ولیدیشن: `utils/error_handler.py` و `utils/validators.py` شامل استثناهای سفارشی و دکوریتور `handle_errors`.
  - پشتیبان‌گیری: `utils/backup_manager.py` با پشتیبان فشرده، تایید سالم بودن، و پشتیبان‌گیری دوره‌ای.
- ربات تلگرام
  - `TelegramBotPremium`: دستورات کاربری و ادمین، جریان آپلود، ترجمه و ارسال فایل خروجی.
- تست‌ها و مثال‌ها
  - دایرکتوری `tests/` شامل تست‌های parser، مدیریت فایل، سرویس ترجمه، و سیستم پریمیوم است.
  - نمونه SRT در `examples/test_subtitle.srt` موجود است.
- وابستگی‌ها
  - `python-telegram-bot==21.4`, `openai==1.40.0`, `pysrt`, `aiofiles`, `pytest`, `python-dotenv`.

---

## 2) مشکلات شناسایی‌شده و اثر آنها

1) آرتیفکت/استاندارد نبودن برخی فایل‌ها (SyntaxError/Invalid inputs)
- `tests/test_translation.py` ابتدای فایل دارای متن اضافه ("قرض") قبل از shebang است که باعث SyntaxError ه��گام جمع‌آوری تست‌ها می‌شود.
- `examples/test_subtitle.srt` خط اول باید عدد «1» باشد ولی متن غیرعددی دارد ("د از 1")؛ اعتبارسنجی SRT را می‌شکند و تست `test_srt_parser` را Fail می‌کند.
- `setup.py` ابتدای فایل دارای متن اضافه ("یاز") قبل از shebang است و اجرای اسکریپت setup را خراب می‌کند.

2) عدم پیاده‌سازی متدهای abstract در OpenAITranslator
- `BaseTranslator` متدهای زیر را abstract تعریف کرده است:
  - `_translate_text_impl`
  - `_translate_batch_impl`
- `OpenAITranslator` این متدها را پیاده‌سازی نکرده و به‌جای آن `translate_text` و `translate_batch` را Override کرده است. نتیجه: در اجرای واقعی، نمونه‌سازی از `OpenAITranslator` با خطای کلاس abstract مواجه می‌شود.
- در تست‌ها این مشکل با Mock پنهان شده است، اما در اجرای Bot واقعی خطا می‌دهد.

3) همراستایی انواع خطا در TranslationService
- در `translate_subtitle_file` در صورت SRT نامعتبر، `Exception` ساده raise می‌شود ("Invalid SRT file format")، در حالی‌که تست `test_translate_subtitle_file_invalid_format` انتظار `FileProcessingError` دارد.
- همچنین بهتر است این متد نیز تحت دکوریتور `@handle_errors` با انواع خطای مربوطه قرار گیرد و از `InputValidator` برای مسیر فایل استفاده کند.

4) بهبود ترتیب نتایج در BaseTranslator.translate_batch
- پیاده‌سازی فعلی با `insert` ممکن است ترتیب ترجمه‌ها را در وجود cacheهای پراکنده دچار پیچیدگی کند. بهتر است یک لیست با طول ثابت از ابتدا ساخته و بر اساس ایندکس‌ها پر شود تا ترتیب دقیق حفظ شود. (این مورد بهبود کیفیت است و فوریت کمتر دارد.)

5) نکات سازگاری و پایداری OpenAI SDK 1.x
- استفاده از `openai.AsyncOpenAI` صحیح است؛ بهتر است `_translate_*_impl`ها با مدیریت خطا/timeout/Retry مناسب تکمیل شوند و caching توسط `BaseTranslator` فعال گردد.

6) کیفیت تست‌های نمایشی
- `tests/test_translation.py` یک اسکریپت نمایشی است و تست `pytest` استاندارد نیست؛ یا باید به pytest تبدیل شود یا حداقل بدون SyntaxError باشد تا فرآیند جمع‌آوری تست را مختل نکند.

---

## 3) نقشه راه مرحله‌به‌مرحله (Plan)

- مرحله 1: اصلاح مشکلات محتوایی/نحوی
  - حذف کاراکترهای زائد از `tests/test_translation.py` و حفظ نقش نمایشی/اطلاعاتی آن.
  - تصحیح `examples/test_subtitle.srt` (خط اول باید «1» باشد).
  - حذف کاراکترهای زائد از `setup.py`.

- مرحله 2: تکمیل OpenAITranslator مطابق BaseTranslator
  - پیاده‌سازی `_translate_text_impl(text, target_language)` با منطق فعلی `translate_text`.
  - پیاده‌سازی `_translate_batch_impl(texts, target_language)` با دو مسیر:
    - دسته کوچک: درخواست یک‌جا (parse شماره‌گذاری‌شده)
    - دسته بزرگ: ترجمه‌های concurrent با Semaphore
  - حذف/عدم Override متدهای `translate_text` و `translate_batch` در کلاس، تا caching لایه پایه (`@cachedmethod` در `BaseTranslator`) فعال باشد.
  - مدیریت خطا/timeout/temperature و لاگ مناسب حفظ شود.

- مرحله 3: همراستاسازی خطاها در TranslationService
  - در `translate_subtitle_file`: در صورت SRT نامعتبر `FileProcessingError` raise شود.
  - سایر خطاهای ترجمه با `TranslationError` نگاشت شوند.
  - استفاده از `InputValidator.validate_file_path` و افزودن/تکمیل `@handle_errors` در متدهای کلیدی.

- مرحله 4: بهبود BaseTranslator.translate_batch (اختیاری اما توصیه‌شده)
  - بازنویسی به تولید لیست خروجی ثابت طول و جای‌گذاری نتایج ایندکسی برای حفظ ترتیب در حضور cache.

- مرحله 5: اجرای تست‌ها و پایدارسازی
  - اجرای `pytest` و رفع هر گونه Failure باقی‌مانده.

- مرحله 6: بهبودهای تکمیلی
  - بازبینی سطوح لاگ و جلوگیری از نشت داده حساس.
  - بروز کردن مستندات و README در صورت نیاز.

---

## 4) چک‌لیست اجرای کارها

- [ ] اصلاح `tests/test_translation.py` (حذف کاراکتر اضافه و تمیزکاری)
- [ ] اصلاح `examples/test_subtitle.srt` (تعویض خط اول به «1»)
- [ ] اصلاح `setup.py` (حذف کاراکتر اضافه)
- [ ] تکمیل `OpenAITranslator` با `_translate_text_impl` و `_translate_batch_impl`
- [ ] حذف Override‌های غیرضروری برای فعال‌سازی caching پایه
- [ ] همراستاسازی خطاها ��ر `TranslationService.translate_subtitle_file`
- [ ] بهبود ترتیب نتایج در `BaseTranslator.translate_batch` (بهبود کیفیت)
- [ ] اجرای `pytest` و تثبیت سبزی تست‌ها

---

## 5) پیشنهادات فنی برای پیاده‌سازی

- OpenAITranslator
  - نمونه‌سازی کلاینت: `self.client = openai.AsyncOpenAI(api_key=config['api_key'])`
  - Prompt: تاکید بر خروجی فقط ترجمه و عدم اضافه کردن توضیحات.
  - دسته‌های کوچک: پاسخ شماره‌گذاری‌شده را به لیست برگردانید؛ در صورت کمبود خطوط، fallback به متن اصلی برای حفظ طول.
  - دسته‌های بزرگ: Semaphore(5) برای محدودیت کانکارنسی؛ `asyncio.gather` برای تجمیع.
  - مدیریت خطا: لاگ با `logger.error` و raise با پیام روشن.

- TranslationService
  - `validate_srt_file` اگر False بود → `FileProcessingError("فرمت فایل SRT نامعتبر است")`.
  - Validation مسیر ورودی با `InputValidator.validate_file_path`.
  - Wrap با `@handle_errors(TranslationError, FileProcessingError, reraise=True)` در متدهای مناسب.

- BaseTranslator.translate_batch
  - ساخت `translated = [None] * len(texts)` و جای‌گذاری بر اساس ایندکس‌ها جهت حفظ ترتیب.

---

## 6) دستورات اجرایی مفید

- نصب وابستگی‌ها:
  ```bash
  pip install -r requirements.txt
  ```

- اجرای راه‌اندازی سریع:
  ```bash
  python setup.py
  ```

- اجرای تست‌ها:
  ```bash
  python -m pytest -q
  ```

- اجرای ربات (پس از تنظیم .env):
  ```bash
  python main.py
  ```

---

## 7) نتیجه مورد انتظار پس از اصلاحات

- جمع‌آوری تست‌ها بدون SyntaxError و موفقیت تست‌های زیر:
  - Parser، مدیریت فایل، سرویس ترجمه و سیستم پریمیوم.
- امکان نمونه‌سازی و استفاده پایدار از `OpenAITranslator` در اجرای واقعی ربات.
- رفتار خطاها در `TranslationService` مطابق انتظار تست‌ها (به‌ویژه `FileProcessingError`).
- بهبود پایداری و قابل‌اعتماد بودن فرآیند ترجمه و مدیریت فایل.

---

## 8) گام بعدی (Next Step)

در ادامه، در «مرحله 1» اصلاحات محتوایی/نحوی را روی سه فایل زیر اعمال خواهیم کرد تا بستر اجرای تست‌ها و تغییرات اصلی آماده شود:
- `tests/test_translation.py`
- `examples/test_subtitle.srt`
- `setup.py`
