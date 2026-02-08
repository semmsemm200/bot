from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        [InlineKeyboardButton("📋 طلب مهمة جديدة", callback_data="new_task")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("📊 مهامي", callback_data="my_tasks")],
        [InlineKeyboardButton("💸 سحب الأرباح", callback_data="withdraw")],
        [InlineKeyboardButton("👥 الإحالات", callback_data="referrals")],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")],
        [InlineKeyboardButton("🎬 فيديو الشرح", callback_data="tutorial")],
    ]
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🔧 لوحة الإدارة", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)
