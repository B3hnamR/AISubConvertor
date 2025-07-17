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

class TelegramBot:
    """Telegram bot for subtitle translation service"""
    
    def __init__(self):
        self.translation_service = TranslationService()
        self.application = None
        self.user_sessions = {}  # Store user session data
        
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
            self.application.add_handler(MessageHandler(filters.Document.FileExtension("srt"), self.handle_srt_file))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
            
            logger.info("Telegram bot setup completed")
            
        except Exception as e:
            logger.error(f"Bot setup failed: {str(e)}")
            raise Exception(f"Bot setup failed: {str(e)}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎬 **خوش آمدید به سرویس ترجمه زیرنویس!**

این ربات فایل‌های زیرنویس SRT شما را به فارسی ترجمه می‌کند.

**نحوه استفاده:**
1️⃣ فایل SRT خود را ارسال کنید
2️⃣ منتظر بمانید تا ترجمه انجام شود
3️⃣ فایل ترجمه شده را دریافت کنید

**دستورات مفید:**
• `/help` - راهنمای کامل
• `/info` - اطلاعات مترجم فعلی
• `/preview` - پیش‌نمایش ترجمه (بعد از ارسال فایل)

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
• پشتیبانی از انواع کدگذاری متن
• ترجمه با کیفیت بالا توسط هوش مصنوعی
• پیش‌نمایش ترجمه قبل از دانلود

**نحوه استفاده:**
1. فایل SRT خود را به ربات ارسال کنید
2. ربات فایل را تجزیه و ترجمه می‌کند
3. فایل ترجمه شده را دریافت کنید

**محدودیت‌ها:**
• حداکثر حجم فایل: {max_size} مگابایت
• فقط فایل‌های SRT پشتیبانی می‌شوند
• زبان مقصد: فارسی

**دستورات:**
• `/start` - شروع مجدد
• `/help` - این راهنما
• `/info` - اطلاعات مترجم
• `/preview` - پیش‌نمایش آخرین ترجمه

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
            """
            
            await update.message.reply_text(
                info_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در دریافت اطلاعات: {str(e)}"
            )
    
    async def preview_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /preview command"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions or 'last_file' not in self.user_sessions[user_id]:
            await update.message.reply_text(
                "❌ هیچ فایلی برای پیش‌نمایش موجود نیست. ابتدا یک فایل SRT ارسال کنید."
            )
            return
        
        try:
            await update.message.reply_text("🔄 در حال تولید پیش‌نمایش...")
            
            last_file_path = self.user_sessions[user_id]['last_file']
            preview = await self.translation_service.get_translation_preview(last_file_path, max_lines=3)
            
            if not preview:
                await update.message.reply_text("❌ امکان تولید پیش‌نمایش وجود ندارد.")
                return
            
            preview_message = "🔍 **پیش‌نمایش ترجمه:**\n\n"
            
            for i, item in enumerate(preview, 1):
                preview_message += f"**{i}. زمان:** `{item['time']}`\n"
                preview_message += f"**متن اصلی:** {item['original']}\n"
                preview_message += f"**ترجمه:** {item['translated']}\n\n"
            
            preview_message += "✅ برای ترجمه کامل فایل، دوباره آن را ارسال کنید."
            
            await update.message.reply_text(
                preview_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Preview failed: {str(e)}")
            await update.message.reply_text(
                f"❌ خطا در تولید پیش‌نمایش: {str(e)}"
            )
    
    async def handle_srt_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle SRT file uploads"""
        try:
            document: Document = update.message.document
            user_id = update.effective_user.id
            
            # Validate file
            if not document.file_name.lower().endswith('.srt'):
                await update.message.reply_text(
                    "❌ فقط فایل‌های SRT پشتیبانی می‌شوند."
                )
                return
            
            if document.file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                await update.message.reply_text(
                    f"❌ حجم فایل بیش از حد مجاز است. حداکثر: {settings.MAX_FILE_SIZE_MB} مگابایت"
                )
                return
            
            # Download file
            await update.message.reply_text("📥 در حال دانلود فایل...")
            
            file = await context.bot.get_file(document.file_id)
            input_file_path = os.path.join(settings.TEMP_DIR, f"{user_id}_{document.file_name}")
            
            await file.download_to_drive(input_file_path)
            
            # Store in user session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id]['last_file'] = input_file_path
            
            # Start translation
            await update.message.reply_text(
                "🔄 در حال ترجمه... این ممکن ا��ت چند دقیقه طول بکشد.\n\n"
                "💡 می‌توانید از دستور `/preview` برای مشاهده پیش‌نمایش استفاده کنید."
            )
            
            # Translate file
            output_file_path = await self.translation_service.translate_subtitle_file(input_file_path)
            
            # Send translated file
            await update.message.reply_text("✅ ترجمه تکمیل شد! در حال ارسال فایل...")
            
            async with aiofiles.open(output_file_path, 'rb') as f:
                file_content = await f.read()
            
            output_filename = f"translated_{document.file_name}"
            await update.message.reply_document(
                document=file_content,
                filename=output_filename,
                caption="🎉 فایل زیرنویس ترجمه شده آماده است!\n\n"
                       "✨ از سرویس ما استفاده کردید، ممنون!"
            )
            
            # Cleanup
            try:
                os.remove(input_file_path)
                os.remove(output_file_path)
            except:
                pass
            
        except Exception as e:
            logger.error(f"File handling failed: {str(e)}")
            await update.message.reply_text(
                f"❌ خطا در پردازش فایل: {str(e)}\n\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        await update.message.reply_text(
            "📝 پیام شما دریافت شد!\n\n"
            "برای ترجمه زیرنویس، لطفاً فایل SRT خود را ارسال کنید.\n"
            "برای راهنما از دستور `/help` استفاده کنید."
        )
    
    async def run_bot(self):
        """Run the bot"""
        try:
            logger.info("Starting Telegram bot...")
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