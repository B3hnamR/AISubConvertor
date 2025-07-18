import logging
import os
import asyncio
import time
from typing import Dict, Any
from telegram import Update, Document, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import aiofiles

from config import settings
from ..services import TranslationService, UserService, AdminService
from ..database import get_database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

class TelegramBotPremium:
    """ربات تلگرام با سیستم اشتراک و مدیریت کاربران"""
    
    def __init__(self):
        self.translation_service = TranslationService()
        self.user_service = UserService()
        self.admin_service = AdminService()
        self.db = get_database()
        self.application = None
        
        # Ensure directories exist
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        # Initialize super admins
        self._init_super_admins()
    
    def _init_super_admins(self):
        """ایجاد سوپر ادمین‌های اولیه"""
        for admin_id in settings.SUPER_ADMIN_IDS:
            if admin_id and not self.db.is_admin(admin_id):
                self.db.add_admin(admin_id, admin_id)  # خودش را اضافه می‌کند
                logger.info(f"Super admin {admin_id} initialized")
    
    def setup_bot(self):
        """Setup the Telegram bot with handlers"""
        try:
            settings.validate()
            
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("profile", self.profile_command))
            self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
            self.application.add_handler(CommandHandler("preview", self.preview_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("cleanup", self.cleanup_command))
            
            # Admin commands
            self.application.add_handler(CommandHandler("admin", self.admin_command))
            self.application.add_handler(CommandHandler("stats", self.admin_stats_command))
            self.application.add_handler(CommandHandler("users", self.admin_users_command))
            self.application.add_handler(CommandHandler("addadmin", self.admin_add_admin_command))
            self.application.add_handler(CommandHandler("grant", self.admin_grant_subscription_command))
            
            # File and callback handlers
            self.application.add_handler(MessageHandler(filters.Document.FileExtension("srt"), self.handle_srt_file))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
            
            logger.info("Premium Telegram bot setup completed")
            
        except Exception as e:
            logger.error(f"Bot setup failed: {str(e)}")
            raise Exception(f"Bot setup failed: {str(e)}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # ثبت‌نام کاربر
        result = await self.user_service.register_user(
            user.id, user.username, user.first_name, user.last_name
        )
        
        if result['is_new']:
            welcome_message = """
🎉 **خوش آمدید به سرویس ترجمه زیرنویس پریمیوم!**

حساب شما با موفقیت ایجاد شد! 

🎁 **هدیه ویژه**: یک ترجمه رایگان در اختیار دارید

**ویژگی‌های سرویس:**
✅ ترجمه دقیق با هوش مصنوعی
✅ حفظ کامل تایمینگ اصلی
✅ پشتیبانی از انواع کدگذاری
✅ مدیریت هوشمند فایل‌ها

**دستورات مفید:**
• `/profile` - مشاهده پروفایل و اشتراک
• `/subscribe` - خرید اشتراک
• `/help` - راهنمای کامل

برای شروع، فایل SRT خود را ارسال کنید! 🚀
            """
        else:
            welcome_message = f"""
👋 **خوش آمدید {user.first_name}!**

شما قبلاً عضو سرویس ما هستید.

• `/profile` - مشاهده پروفایل شما
• `/subscribe` - مدیریت اشتراک
• `/help` - راهنمای کامل

فایل SRT خود را ارسال کنید تا شروع کنیم! 🎬
            """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        user_id = update.effective_user.id
        
        profile = await self.user_service.get_user_profile(user_id)
        if not profile:
            await update.message.reply_text(
                "❌ پروفایل یافت نشد. لطفاً ابتدا /start را بزنید."
            )
            return
        
        # ساخت پیام پروفایل
        profile_message = f"""
👤 **پروفایل کاربری**

**اطلاعات کلی:**
• نام: {profile.get('first_name', 'نامشخص')}
• نام کاربری: @{profile.get('username', 'ندارد')}
• نقش: {self._get_role_emoji(profile['role'])} {self._get_role_name(profile['role'])}
• تاریخ عضویت: {profile['created_at'][:10]}

**آمار ترجمه:**
• کل ��رجمه‌ها: {profile['total_translations']}
• ترجمه‌های رایگان استفاده شده: {profile['free_translations_used']}/{settings.FREE_TRANSLATIONS_LIMIT}
        """
        
        # اطلاعات اشتراک
        if profile['subscription']:
            sub = profile['subscription']
            profile_message += f"""

**اشتراک فعال:**
• نوع: {self._get_plan_name(sub['plan_type'])}
• وضعیت: ✅ فعال
• باقی‌مانده: {sub['remaining_days']} روز
• تاریخ انقضا: {sub['end_date'][:10]}
            """
        else:
            remaining_free = settings.FREE_TRANSLATIONS_LIMIT - profile['free_translations_used']
            if remaining_free > 0:
                profile_message += f"""

**وضعیت فعلی:**
• ترجمه‌های رایگان باقی‌مانده: {remaining_free}
• برای ترجمه نامحدود، اشتراک تهیه کنید
                """
            else:
                profile_message += f"""

**وضعیت فعلی:**
• ترجمه‌های رایگان تمام شده
• برای ادامه، اشتراک تهیه کنید
                """
        
        # دکمه‌های عملیات
        keyboard = []
        if not profile['subscription'] or profile['subscription']['remaining_days'] < 7:
            keyboard.append([InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscribe")])
        
        keyboard.append([InlineKeyboardButton("🔄 بهروزرسانی", callback_data="refresh_profile")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            profile_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        plans = await self.user_service.get_subscription_plans()
        
        subscribe_message = """
💳 **طرح‌های اشتراک**

برای استفاده نامحدود از سرویس، یکی از طرح‌های زیر را انتخاب کنید:
        """
        
        keyboard = []
        for plan_id, plan in plans.items():
            plan_text = f"{plan['name']} - {plan['price']:,} تومان"
            keyboard.append([InlineKeyboardButton(plan_text, callback_data=f"buy_{plan_id}")])
        
        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            subscribe_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_srt_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle SRT file uploads with subscription check"""
        try:
            document: Document = update.message.document
            user_id = update.effective_user.id
            start_time = time.time()
            
            # بررسی مجوز ترجمه
            permission = await self.user_service.check_translation_permission(user_id)
            
            if not permission['allowed']:
                if permission['reason'] == 'subscription_required':
                    # نمایش پیام نیاز به اشتراک
                    message = f"""
❌ **ترجمه رایگان شما تمام شده است**

{permission['message']}

💡 **راه‌حل‌ها:**
• خرید اشتراک برای ترجمه نامحدود
• استفاده از کیفیت بالا و سرعت بیشتر

برای مشاهده طرح‌های اشتراک از دستور `/subscribe` استفاده کنید.
                    """
                    
                    keyboard = [[InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscribe")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(permission['message'])
                return
            
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
            
            # پیام شروع پردازش
            status_message = f"""
📥 **شروع پردازش فایل**

📄 نام: {document.file_name}
📊 حجم: {document.file_size / 1024:.1f} کیلوبایت
👤 نوع حساب: {permission['type'].upper()}
🆔 شناسه: {file_info['file_id'][:8]}...

⏳ در حال دانلود...
            """
            
            status_msg = await update.message.reply_text(
                status_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # دانلود فایل
            await self.translation_service.file_manager.start_file_download(user_id)
            file = await context.bot.get_file(document.file_id)
            await file.download_to_drive(file_info['file_path'])
            await self.translation_service.file_manager.complete_file_download(user_id)
            
            # بهروزرسانی وضعیت
            await status_msg.edit_text(
                status_message.replace("⏳ در حال دانلود...", "🔄 در حال ترجمه..."),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # پردازش فایل
            output_file_path = await self.translation_service.process_user_file(
                user_id, file_info['file_path']
            )
            
            # ثبت استفاده
            processing_time = time.time() - start_time
            await self.user_service.use_translation(
                user_id, document.file_name, document.file_size, processing_time
            )
            
            # ارسال فایل ترجمه شده
            await status_msg.edit_text(
                "✅ ترجمه تکمیل شد! در حال ارسال فایل...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            async with aiofiles.open(output_file_path, 'rb') as f:
                file_content = await f.read()
            
            output_filename = f"translated_{document.file_name}"
            
            # پیام نهایی بر اساس نوع حساب
            if permission['type'] == 'free':
                remaining = permission.get('remaining_free', 0) - 1
                caption = f"""
🎉 **ترجمه تکمیل شد!**

✨ تایمینگ اصلی حفظ شده
⏱️ زمان پردازش: {processing_time:.1f} ثانیه

🆓 ترجمه‌های رایگان باقی‌مانده: {remaining}

💡 برای ترجمه نامحدود، اشتراک تهیه کنید!
                """
            else:
                caption = f"""
🎉 **ترجمه تکمیل شد!**

✨ تایمینگ اصلی حفظ شده
⏱️ زمان پردازش: {processing_time:.1f} ثانیه
👑 حساب پریمیوم - ترجمه نامحدود

🙏 از سرویس ما استفاده کردید، ممنون!
                """
            
            await update.message.reply_document(
                document=file_content,
                filename=output_filename,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # حذف پیام وضعیت
            try:
                await status_msg.delete()
            except:
                pass
            
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
                "📞 در صورت تکرار مشکل، با پشتیبانی تماس بگیرید."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "subscribe":
            await self.subscribe_command(update, context)
        
        elif data.startswith("buy_"):
            plan_type = data.replace("buy_", "")
            
            # شبیه‌سازی خرید اشتراک
            result = await self.user_service.create_subscription(user_id, plan_type)
            
            if result['success']:
                await query.edit_message_text(
                    f"✅ {result['message']}\n\n"
                    "حالا می‌توانید از ترجمه نامحدود استفاده کنید!",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(
                    f"❌ {result['message']}",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif data == "refresh_profile":
            # بهروزرسانی پروفایل
            await self.profile_command(update, context)
        
        elif data == "cancel":
            await query.edit_message_text("❌ عملیات لغو شد.")
    
    # Admin Commands
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if not await self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ شما مجوز دسترسی به پنل ادمین ندارید.")
            return
        
        admin_message = """
🔧 **پنل مدیریت**

**دستورات موجود:**
• `/stats` - آمار سیستم
• `/users` - لیست کاربران
• `/addadmin [user_id]` - اضافه کردن ادمین
• `/grant [user_id] [plan]` - اعطای اشتراک

**مثال:**
• `/addadmin 123456789`
• `/grant 123456789 monthly`
        """
        
        await update.message.reply_text(
            admin_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        if not await self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
            return
        
        stats = await self.admin_service.get_system_stats()
        
        stats_message = f"""
📊 **آمار سیستم**

**کاربران:**
• کل: {stats['users']['total']}
• پریمیوم: {stats['users']['premium']}
• رایگان: {stats['users']['free']}

**تراکنش‌ها:**
• کل: {stats['transactions']['total']}
• هفته گذشته: {stats['transactions']['weekly']}

**درآمد:**
• کل: {stats['revenue']['total']:,} تومان
        """
        
        await update.message.reply_text(
            stats_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command"""
        user_id = update.effective_user.id
        
        if not await self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
            return
        
        result = await self.admin_service.get_users_list(page=1, per_page=10)
        
        if not result['success']:
            await update.message.reply_text("❌ خطا در دریافت لیست کاربران.")
            return
        
        users_message = "👥 **لیست کاربران (10 کاربر اخیر):**\n\n"
        
        for user in result['users']:
            role_emoji = self._get_role_emoji(user['role'])
            users_message += f"{role_emoji} {user['user_id']} - {user.get('first_name', 'نامشخص')}\n"
        
        await update.message.reply_text(
            users_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addadmin command"""
        user_id = update.effective_user.id
        
        if not await self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("❌ استفاده: /addadmin [user_id]")
            return
        
        try:
            target_user_id = int(context.args[0])
            result = await self.admin_service.add_admin(target_user_id, user_id)
            await update.message.reply_text(result['message'])
        except ValueError:
            await update.message.reply_text("❌ شناسه کاربر نامعتبر.")
    
    async def admin_grant_subscription_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grant command"""
        user_id = update.effective_user.id
        
        if not await self.admin_service.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
            return
        
        if len(context.args) != 2:
            await update.message.reply_text("❌ استفاده: /grant [user_id] [monthly|yearly]")
            return
        
        try:
            target_user_id = int(context.args[0])
            plan_type = context.args[1]
            
            result = await self.admin_service.grant_subscription(target_user_id, plan_type, user_id)
            await update.message.reply_text(result['message'])
        except ValueError:
            await update.message.reply_text("❌ شناسه کاربر نامعتبر.")
    
    # Helper methods
    def _get_role_emoji(self, role: str) -> str:
        """دریافت ایموجی نقش"""
        emojis = {
            'admin': '👑',
            'premium': '💎',
            'free': '🆓'
        }
        return emojis.get(role, '❓')
    
    def _get_role_name(self, role: str) -> str:
        """دریافت نام نقش"""
        names = {
            'admin': 'مدیر',
            'premium': 'پریمیوم',
            'free': 'رایگان'
        }
        return names.get(role, 'نامشخص')
    
    def _get_plan_name(self, plan_type: str) -> str:
        """دریافت نام طرح اشتراک"""
        names = {
            'monthly': 'ماهانه',
            'yearly': 'سالانه'
        }
        return names.get(plan_type, 'نامشخص')
    
    # Other commands (preview, status, cleanup, help, handle_text)
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
                preview_message += f"**ترجمه:** {item['translated']}\n\n"
            
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
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            user_id = update.effective_user.id
            
            # دریافت وضعیت کاربر
            user_file_info = await self.translation_service.file_manager.get_user_file_info(user_id)
            can_upload = await self.translation_service.can_user_upload(user_id)
            permission = await self.user_service.check_translation_permission(user_id)
            
            if user_file_info:
                status_message = f"""
📊 **وضعیت فایل فعلی:**

**فایل:** {user_file_info['original_filename']}
**وضعیت:** {user_file_info['status']}
**حجم:** {user_file_info['file_size'] / 1024:.1f} کیلوبایت
**زمان ایجاد:** {user_file_info['created_at'].strftime('%H:%M:%S')}

**مجوز ترجمه:** {'✅ دارد' if permission['allowed'] else '❌ ندارد'}
**نوع حساب:** {permission.get('type', 'نامشخص').upper()}
                """
            else:
                status_message = f"""
📊 **وضعیت شما:**

**فایل فعال:** ندارید
**آماده آپلود:** {'✅ بله' if can_upload else '❌ خیر'}
**مجوز ترجمه:** {'✅ دارد' if permission['allowed'] else '❌ ندارد'}
**نوع حساب:** {permission.get('type', 'نامشخص').upper()}

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
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 **راهنمای سرویس ترجمه زیرنویس پریمیوم**

**دستورات کاربری:**
• `/start` - شروع و ثبت‌نام
• `/profile` - مشاهده پروفایل و اشتراک
• `/subscribe` - خرید اشتراک
• `/preview` - پیش��نمایش ترجمه
• `/status` - وضعیت فایل فعلی
• `/cleanup` - پاکسازی فایل‌ها
• `/help` - این راهنما

**نحوه استفاده:**
1. فایل SRT خود را ارسال کنید
2. منتظر بمانید تا ترجمه انجام شود
3. فایل ترجمه شده را دریافت کنید

**ویژگی‌ها:**
✅ حفظ دقیق تایمینگ اصلی
✅ ترجمه با کیفیت بالا
✅ پشتیبانی از انواع کدگذاری
✅ مدیریت هوشمند فایل‌ها

**طرح‌های اشتراک:**
🆓 رایگان: 1 ترجمه
💎 ماهانه: ترجمه نامحدود
👑 سالانه: ترجمه نامحدود + تخفیف

برای خرید اشتراک از `/subscribe` استفاده کنید.
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        await update.message.reply_text(
            "📝 پیام شما دریافت شد!\n\n"
            "برای ترجمه زیرنویس، لطفاً فایل SRT خود را ارسال کنید.\n"
            "برای مشاهده راهنما ا�� `/help` استفاده کنید.\n"
            "برای مشاهده پروفایل از `/profile` استفاده کنید."
        )
    
    async def run_bot(self):
        """Run the bot"""
        try:
            logger.info("Starting premium Telegram bot...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Premium bot is running! Press Ctrl+C to stop.")
            
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