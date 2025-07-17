import logging
import os
import asyncio
from typing import Dict, Any
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import aiofiles

from config import settings
from ..services import TranslationService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

class TelegramBotImproved:
    """Telegram bot for subtitle translation service with advanced file management"""
    
    def __init__(self):
        self.translation_service = TranslationService()
        self.application = None
        
        # Ensure directories exist
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    def setup_bot(self):
        """Setup the Telegram bot with handlers"""
        try:
            settings.validate()
            
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("info", self.info_command))
            self.application.add_handler(CommandHandler("preview", self.preview_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("cleanup", self.cleanup_command))
            self.application.add_handler(MessageHandler(filters.Document.FileExtension("srt"), self.handle_srt_file))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
            
            logger.info("Telegram bot setup completed")
            
        except Exception as e:
            logger.error(f"Bot setup failed: {str(e)}")
            raise Exception(f"Bot setup failed: {str(e)}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎬 **خوش آمدید به سرویس ترجمه زیرنویس پ��شرفته!**

این ربات فایل‌های زیرنویس SRT شما را با حفظ دقیق تایمینگ به فارسی ترجمه می‌کند.

**ویژگی‌های جدید:**
✅ مدیریت هوشمند فایل‌ها
✅ حفظ کامل تایمینگ اصلی
✅ جلوگیری از تداخل کاربران
✅ پاکسازی خودکار فضا

**نحوه استفاده:**
1️⃣ فایل SRT خود را ارسال کنید
2️⃣ منتظر بمانید تا ترجمه انجام شود
3️⃣ فایل ترجمه شده را دریافت کنید

**دستورات مفید:**
• `/help` - راهنمای کامل
• `/info` - اطلاعات مترجم فعلی
• `/preview` - پیش‌نمایش ترجمه
• `/status` - وضعیت سیستم
• `/cleanup` - پاکسازی فایل‌های شما

فایل SRT خود را ارسال کنید تا شروع کنیم! 🚀
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 **راهنمای استفاده از ربات ترجمه زیرنویس**

**قابلیت‌های ربات:**
• ترجمه فایل‌های SRT به فارسی
• حفظ دقیق تایمینگ اصلی
• مدیریت هوشمند فضای ذخیره‌سازی
• جلوگیری از تداخل پردازش
• پاکسازی خودکار فایل‌ها

**نحوه استفاده:**
1. فایل SRT خود را به ربات ارسال کنید
2. ربات فایل را در فضای اختصاصی شما ذخیره می‌کند
3. تایمینگ حفظ شده و فقط متن‌ها ترجمه می‌شوند
4. فایل ترجمه شده را دریافت کنید

**محدودیت‌ها:**
• حداکثر حجم فایل: {max_size} مگابایت
• یک فایل همزمان برای هر کاربر
• فقط فایل‌های SRT پشتیبانی می‌شوند
• زبان مقصد: فارسی

**دستورات:**
• `/start` - شروع مجدد
• `/help` - این راهنما
• `/info` - اطلاعات مترجم
• `/preview` - پیش‌نمایش آخرین ترجمه
• `/status` - وضعیت سیستم
• `/cleanup` - پاکسازی فایل‌های شما

**امنیت و حریم خصوصی:**
• فایل‌ها در فضای جداگانه هر کاربر ذخیره می‌شوند
• پاکسازی خودکار بعد از 5 دقیقه
• عدم تداخل با سایر کاربران

❓ **سوال یا مشکل دارید؟**
با ارسال پیام متنی با ما در تماس باشید.
        """.format(max_size=settings.MAX_FILE_SIZE_MB)
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
        try:
            translator_info = self.translation_service.get_translator_info()
            
            info_message = f"""
🤖 **اطلاعات مترجم فعلی**

**ارائه‌دهنده:** {translator_info.get('provider', 'نامشخص')}
**زبان مقصد:** {translator_info.get('target_language', 'فارسی')}

**ارائه‌دهندگان موجود:**
{', '.join(translator_info.get('available_providers', []))}

**تنظیمات:**
• حداکثر حجم فایل: {settings.MAX_FILE_SIZE_MB} MB
• فرمت پشتیبانی شده: SRT
• حفظ تایمینگ: ✅ فعال
• مدیریت فایل: ✅ پیشرفته
            """
            
            await update.message.reply_text(
                info_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در دریافت اطلاعات: {str(e)}"
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            user_id = update.effective_user.id
            
            # دریافت وضعیت کاربر
            user_file_info = await self.translation_service.file_manager.get_user_file_info(user_id)
            can_upload = await self.translation_service.can_user_upload(user_id)
            
            # دریافت وضعیت سیستم
            system_status = await self.translation_service.get_system_status()
            
            if user_file_info:
                status_message = f"""
📊 **وضعیت شما:**

**فایل فعال:** {user_file_info['original_filename']}
**وضعیت:** {user_file_info['status']}
**حجم:** {user_file_info['file_size'] / 1024:.1f} کیلوبایت
**زمان ایجاد:** {user_file_info['created_at'].strftime('%H:%M:%S')}

**وضعیت سیستم:**
• فایل‌های فعال: {system_status['file_manager']['active_files']}
• حجم کل: {system_status['file_manager']['total_size_mb']} مگابایت
• مترجم: {system_status['translator']['provider']}
                """
            else:
                status_message = f"""
📊 **وضعیت شما:**

**فایل فعال:** ندارید
**آماده آپلود:** {'✅ بله' if can_upload else '❌ خیر'}

**وضعیت سیستم:**
• فایل‌های فعال: {system_status['file_manager']['active_files']}
• حجم کل: {system_status['file_manager']['total_size_mb']} مگابایت
• مترجم: {system_status['translator']['provider']}

💡 می‌توانید فایل SRT جدید ارسال کنید.
                """
            
            await update.message.reply_text(
                status_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در دریافت وضعیت: {str(e)}"
            )
    
    async def cleanup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cleanup command"""
        try:
            user_id = update.effective_user.id
            
            success = await self.translation_service.cleanup_user_data(user_id)
            
            if success:
                await update.message.reply_text(
                    "🧹 فایل‌های شما با موفقیت پاک شدند.\n"
                    "✅ حالا می‌توانید فایل جدید ارسال کنید."
                )
            else:
                await update.message.reply_text(
                    "ℹ️ هیچ فایلی برای پاکسازی یافت نشد."
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در پاکسازی: {str(e)}"
            )
    
    async def preview_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /preview command"""
        user_id = update.effective_user.id
        
        try:
            await update.message.reply_text("🔄 در حال تولید پیش‌نمایش...")
            
            preview = await self.translation_service.get_user_preview(user_id, max_lines=3)
            
            if not preview:
                await update.message.reply_text(
                    "❌ هیچ فایلی برای پیش‌نمایش موجود نیست.\n"
                    "ابتدا یک فایل SRT ارسال کنید."
                )
                return
            
            preview_message = "🔍 **پیش‌نمایش ترجمه:**\n\n"
            
            for item in preview:
                preview_message += f"**{item['index']}. زمان:** `{item['timing']}`\n"
                preview_message += f"**متن اصلی:** {item['original']}\n"
                preview_message += f"**ترجمه:** {item['translated']}\n"
                preview_message += f"**مدت:** {item['duration_ms']}ms\n\n"
            
            preview_message += "✅ برای ترجمه کامل فایل، دوباره آن را ارسال کنید."
            
            await update.message.reply_text(
                preview_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Preview failed for user {user_id}: {str(e)}")
            await update.message.reply_text(
                f"❌ خطا در تولید پیش‌نمایش: {str(e)}"
            )
    
    async def handle_srt_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle SRT file uploads with advanced file management"""
        try:
            document: Document = update.message.document
            user_id = update.effective_user.id
            
            # بررسی امکان آپلود
            can_upload = await self.translation_service.can_user_upload(user_id)
            if not can_upload:
                await update.message.reply_text(
                    "⏳ شما در حال حاضر فایل دیگری در حال پردازش دارید.\n"
                    "لطفاً منتظر بمانید تا پردازش تکمیل شود یا از `/cleanup` استفاده کنید."
                )
                return
            
            # اعتبارسنجی فایل
            if not document.file_name.lower().endswith('.srt'):
                await update.message.reply_text(
                    "❌ فقط فایل‌های SRT پشتیبانی می‌شوند."
                )
                return
            
            # آماده‌سازی آپلود
            try:
                file_info = await self.translation_service.prepare_file_upload(
                    user_id, document.file_name, document.file_size
                )
            except Exception as e:
                await update.message.reply_text(f"❌ {str(e)}")
                return
            
            # شروع دانلود
            await update.message.reply_text(
                f"📥 در حال دانلود فایل...\n"
                f"📄 نام: {document.file_name}\n"
                f"📊 حجم: {document.file_size / 1024:.1f} کیلوبایت\n"
                f"🆔 شناسه فایل: {file_info['file_id'][:8]}..."
            )
            
            await self.translation_service.file_manager.start_file_download(user_id)
            
            # دانلود فایل
            file = await context.bot.get_file(document.file_id)
            await file.download_to_drive(file_info['file_path'])
            
            # تکمیل دانلود
            await self.translation_service.file_manager.complete_file_download(user_id)
            
            # شروع ترجمه
            await update.message.reply_text(
                "🔄 فایل دانلود شد! در حال شروع ترجمه...\n\n"
                "⏱️ این ممکن است چند دقیقه طول بکشد.\n"
                "💡 می‌توانید از دستور `/preview` برای مشاهده پیش‌نمایش استفاده کنید.\n"
                "📊 از `/status` برای مشاهده وضعیت استفاده کنید."
            )
            
            # پردازش فایل
            output_file_path = await self.translation_service.process_user_file(
                user_id, file_info['file_path']
            )
            
            # ارسال فایل ترجمه شده
            await update.message.reply_text("✅ ترجمه تکمیل شد! در حال ارسال فایل...")
            
            async with aiofiles.open(output_file_path, 'rb') as f:
                file_content = await f.read()
            
            output_filename = f"translated_{document.file_name}"
            await update.message.reply_document(
                document=file_content,
                filename=output_filename,
                caption="🎉 فایل زیرنویس ترجمه شده آماده است!\n\n"
                       "✨ تایمینگ اصلی حفظ شده و فقط متن‌ها ترجمه شده‌اند.\n"
                       "🧹 فایل‌ها به صورت خودکار پاک خواهند شد.\n"
                       "🙏 از سرویس ما استفاده کردید، ممنون!"
            )
            
            # پاکسازی خودکار (بعد از 5 دقیقه)
            # فایل‌ها به صورت خودکار پاک می‌شوند
            
        except Exception as e:
            logger.error(f"File handling failed for user {user_id}: {str(e)}")
            
            # پاکسازی در صورت خطا
            try:
                await self.translation_service.cleanup_user_data(user_id)
            except:
                pass
            
            await update.message.reply_text(
                f"❌ خطا در پردازش فایل: {str(e)}\n\n"
                "🔄 لطفاً دوباره تلاش کنید.\n"
                "📞 در صورت تکرار مشکل، با پشتیبانی تماس بگیرید.\n"
                "🧹 از `/cleanup` برای پاکسازی استفاده کنید."
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        await update.message.reply_text(
            "📝 پیام شما دریافت شد!\n\n"
            "برای ترجمه زیرنویس، لطفاً فایل SRT خود را ارسال کنید.\n"
            "برای راهنما از دستور `/help` استفاده کنید.\n"
            "برای مشاهده وضعیت از `/status` استفاده کنید."
        )
    
    async def run_bot(self):
        """Run the bot"""
        try:
            logger.info("Starting advanced Telegram bot...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Bot is running! Press Ctrl+C to stop.")
            
            # Keep the bot running
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot runtime error: {str(e)}")
        finally:
            await self.application.stop()
    
    def run(self):
        """Run the bot (synchronous wrapper)"""
        self.setup_bot()
        asyncio.run(self.run_bot())