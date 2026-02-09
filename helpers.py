from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from config import CHANNEL_ID, CHANNEL_LINK, ADMIN_ID
import db


async def check_channel_member(bot, user_id):
    """Check if user is a member of the channel"""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is subscribed to channel, return True if subscribed, False otherwise"""
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        return False
    
    # Check if user exists in database
    user = db.get_user(user_id)
    if not user:
        # User not registered, show subscription message
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="verify_subscription")]]
        msg = (
            "🔔 مرحباً بك!\n\n"
            "للاستمرار في استخدام البوت، يجب عليك الاشتراك في قناة التحديثات والأخبار أولاً.\n\n"
            "📢 اضغط على الزر بالأسفل للاشتراك، ثم اضغط 'تحققت من الاشتراك'"
        )
        if update.callback_query:
            await update.callback_query.answer("⚠️ يجب الاشتراك في القناة أولاً", show_alert=True)
            await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.message:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return False
    
    # User exists, verify they're still subscribed
    try:
        is_member = await check_channel_member(context.bot, user_id)
    except Exception as e:
        # If channel check fails, allow user to continue
        print(f"Channel check failed in require_subscription: {e}")
        return True
    
    if not is_member:
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="verify_subscription")]]
        msg = (
            "⚠️ يجب عليك الاشتراك في قناة التحديثات والأخبار للاستمرار في استخدام البوت.\n\n"
            "📢 اضغط على الزر بالأسفل للاشتراك، ثم اضغط 'تحققت من الاشتراك'"
        )
        if update.callback_query:
            await update.callback_query.answer("⚠️ يجب الاشتراك في القناة أولاً", show_alert=True)
            await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.message:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return False
    
    return True


def is_admin(user_id):
    return db.is_admin(user_id, ADMIN_ID)


def get_all_admin_ids():
    ids = db.get_admins()
    if ADMIN_ID not in ids:
        ids.append(ADMIN_ID)
    return ids


async def send_to_admins(context, text, reply_markup=None):
    for aid in get_all_admin_ids():
        try:
            await context.bot.send_message(aid, text, reply_markup=reply_markup)
        except Exception:
            pass


async def send_photo_to_admins(context, photo, caption, reply_markup=None):
    for aid in get_all_admin_ids():
        try:
            await context.bot.send_photo(aid, photo, caption=caption, reply_markup=reply_markup)
        except Exception:
            pass


def bot_is_active():
    val = db.get_setting("bot_active")
    return val == "1"


def get_main_menu_keyboard(user_id):
    keyboard = [
        [KeyboardButton("📋 طلب مهمة جديدة"), KeyboardButton("💰 رصيدي")],
        [KeyboardButton("📊 مهامي"), KeyboardButton("💸 سحب الأرباح")],
        [KeyboardButton("👥 الإحالات"), KeyboardButton("💎 سحب رصيد الإحالات")],
        [KeyboardButton("🎬 طريقة عمل المهمة"), KeyboardButton("ℹ️ مساعدة")],
    ]
    if is_admin(user_id):
        keyboard.append([KeyboardButton("🔧 لوحة الإدارة")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
