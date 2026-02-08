from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db
from config import ADMIN_ID, CHANNEL_LINK
from helpers import (
    check_channel_member, is_admin, bot_is_active,
    get_main_menu_keyboard, send_to_admins, send_photo_to_admins
)

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    # Handle referral link: /start ref_12345
    referrer_id = 0
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].replace("ref_", ""))
            if referrer_id == user_id:
                referrer_id = 0
        except ValueError:
            referrer_id = 0

    # Check channel membership
    is_member = await check_channel_member(context.bot, user_id)
    if not is_member:
        keyboard = [[InlineKeyboardButton("📢 انضم للقناة", url=CHANNEL_LINK)],
                     [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text(
            "⚠️ يجب عليك الانضمام لقناة البوت أولاً للاستخدام.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # Save referrer in context for later
        context.user_data["pending_referrer"] = referrer_id
        return

    # Register user
    db.add_user(user_id, username, referrer_id)
    if referrer_id and referrer_id != user_id:
        referrer = db.get_user(referrer_id)
        if referrer:
            db.add_referral(referrer_id, user_id)

    msg = "مرحباً، كل شيء هنا بسيط وسهل، ستقوم بعمل مهمات مقابل مكافأة."
    await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard(user_id))


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name

    is_member = await check_channel_member(context.bot, user_id)
    if not is_member:
        await query.answer("❌ لم تنضم للقناة بعد!", show_alert=True)
        return

    referrer_id = context.user_data.get("pending_referrer", 0)
    db.add_user(user_id, username, referrer_id)
    if referrer_id and referrer_id != user_id:
        referrer = db.get_user(referrer_id)
        if referrer:
            db.add_referral(referrer_id, user_id)

    msg = "مرحباً، كل شيء هنا بسيط وسهل، ستقوم بعمل مهمات مقابل مكافأة."
    await query.edit_message_text(msg, reply_markup=get_main_menu_keyboard(user_id))


# ==================== MENU ====================
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_channel_member(context.bot, user_id)
    if not is_member:
        keyboard = [[InlineKeyboardButton("📢 انضم للقناة", url=CHANNEL_LINK)],
                     [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ يجب عليك الانضمام لقناة البوت أولاً.",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("اختر من القائمة:", reply_markup=get_main_menu_keyboard(user_id))


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text("اختر من القائمة:", reply_markup=get_main_menu_keyboard(user_id))


# ==================== NEW TASK ====================
async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not bot_is_active():
        await query.edit_message_text("⚠️ البوت متوقف حالياً. يرجى المحاولة لاحقاً.")
        return

    price = int(db.get_setting("task_price") or 10)
    task_id = db.create_task(user_id, price)

    await query.edit_message_text(
        f"✅ تم طلب مهمة جديدة.\n"
        f"💰 سعر المهمة: {price} وحدة\n"
        f"⏳ في انتظار بيانات المهمة من المشرف..."
    )

    # Notify admins
    keyboard = [[InlineKeyboardButton("📤 إرسال بيانات المهمة", callback_data=f"admin_send_data_{task_id}")]]
    await send_to_admins(context,
        f"📋 طلب مهمة جديدة\n"
        f"👤 المستخدم: {user_id}\n"
        f"🆔 Task ID: {task_id}\n"
        f"💰 السعر: {price} وحدة\n\n"
        f"يرجى إرسال بيانات المهمة.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== TASK: Admin sends data ====================
async def admin_send_task_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not is_admin(user_id):
        return

    task_id = int(query.data.split("_")[-1])
    context.user_data["admin_sending_data_for_task"] = task_id
    await query.edit_message_text(f"📝 أرسل بيانات المهمة #{task_id} الآن (رسالة نصية):")


# ==================== TASK: User completed ====================
async def task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[-1])
    context.user_data["submitting_proof_for_task"] = task_id
    await query.edit_message_text(
        f"📸 أرسل إثبات إتمام المهمة #{task_id} (صورة/سكرين شوت):"
    )


# ==================== TASK: User cancels ====================
async def task_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[-1])
    db.cancel_task(task_id)
    await query.edit_message_text(f"❌ تم إلغاء المهمة #{task_id}.")


# ==================== TASK: How to do ====================
async def task_how_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_id = db.get_setting("tutorial_video_id")
    if video_id:
        await context.bot.send_video(query.from_user.id, video_id, caption="🎬 فيديو شرح طريقة عمل المهمة")
    else:
        await context.bot.send_message(query.from_user.id, "⚠️ لم يتم تحديد فيديو الشرح بعد.")


# ==================== TASK: Admin approves proof ====================
async def admin_approve_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    task_id = int(query.data.split("_")[-1])
    task = db.get_task(task_id)
    if not task:
        await query.edit_message_text("❌ المهمة غير موجودة.")
        return

    db.approve_task(task_id)
    db.add_to_reserved(task["user_id"], task["price"])

    # Referral reward
    user = db.get_user(task["user_id"])
    if user and user["referrer_id"]:
        reward = int(db.get_setting("referral_reward") or 2)
        db.add_to_referral_balance(user["referrer_id"], reward)

    await query.edit_message_text(f"✅ تمت الموافقة على المهمة #{task_id}.\nالرصيد أُضيف للرصيد المحجوز.")
    await context.bot.send_message(task["user_id"],
        f"✅ تمت الموافقة على المهمة #{task_id}!\n"
        f"💰 تم إضافة {task['price']} وحدة للرصيد المحجوز.\n"
        f"⏳ سيتحول للرصيد المتاح بعد 48 ساعة."
    )


# ==================== TASK: Admin rejects proof ====================
async def admin_reject_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    task_id = int(query.data.split("_")[-1])
    db.reject_task(task_id)
    task = db.get_task(task_id)

    await query.edit_message_text(f"❌ تم رفض المهمة #{task_id}.")
    if task:
        await context.bot.send_message(task["user_id"],
            f"❌ تم رفض المهمة #{task_id}.\nلن يتم إضافة مكافأة."
        )


# ==================== TASK: Admin reports error ====================
async def admin_error_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    task_id = int(query.data.split("_")[-1])
    context.user_data["admin_error_task_id"] = task_id
    await query.edit_message_text(f"📝 أرسل وصف الخطأ في المهمة #{task_id}:")


# ==================== BALANCE ====================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = db.get_user(user_id)
    if not user:
        await query.edit_message_text("⚠️ لم يتم العثور على حسابك.")
        return

    keyboard = [
        [InlineKeyboardButton("📜 سجل السحوبات", callback_data="withdrawal_history")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")],
    ]
    msg = (
        f"🆔 ID: {user['id']}\n"
        f"💰 رصيد متاح: {user['available']} وحدة\n"
        f"🔒 رصيد محجوز: {user['reserved']} وحدة\n"
        f"👥 رصيد الإحالات: {user['referral_balance']} وحدة\n\n"
        f"⏳ الرصيد المحجوز يتحول لرصيد متاح بعد 48 ساعة."
    )
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== MY TASKS ====================
async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    stats = db.get_user_task_stats(user_id)
    tasks_list = db.get_user_tasks(user_id)

    msg = (
        f"📊 إحصائيات مهامك:\n"
        f"📋 إجمالي المهام: {stats['total']}\n"
        f"✅ مهام مقبولة: {stats['approved']}\n"
        f"❌ مهام مرفوضة: {stats['rejected']}\n\n"
    )

    if tasks_list:
        msg += "📝 آخر المهام:\n"
        status_map = {
            "pending": "⏳ معلقة",
            "data_sent": "📤 بيانات مرسلة",
            "proof_submitted": "📸 إثبات مرسل",
            "approved": "✅ مقبولة (محجوز)",
            "released": "✅ مقبولة (متاح)",
            "rejected": "❌ مرفوضة",
            "cancelled": "🚫 ملغاة",
            "error": "⚠️ خطأ",
            "error_resubmitted": "📸 إثبات معاد",
        }
        for t in tasks_list[:10]:
            status_text = status_map.get(t["status"], t["status"])
            msg += f"  #{t['id']} - {t['price']} وحدة - {status_text}\n"

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== WITHDRAWAL ====================
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = db.get_user(user_id)

    if not user:
        await query.edit_message_text("⚠️ لم يتم العثور على حسابك.")
        return

    total_available = user["available"]
    min_withdrawal = int(db.get_setting("min_withdrawal") or 50)

    if total_available < min_withdrawal:
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]]
        await query.edit_message_text(
            f"⚠️ رصيدك المتاح ({total_available} وحدة) أقل من الحد الأدنى للسحب ({min_withdrawal} وحدة).",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    methods = db.get_withdrawal_methods()
    keyboard = []
    for m in methods:
        keyboard.append([InlineKeyboardButton(
            f"{m['name']} (حد أدنى: {m['min_amount']})",
            callback_data=f"wmethod_{m['name']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")])

    await query.edit_message_text(
        f"💸 رصيدك المتاح: {total_available} وحدة\nاختر طريقة السحب:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def withdraw_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    method_name = query.data.replace("wmethod_", "")

    user = db.get_user(user_id)
    method = db.get_withdrawal_method(method_name)

    if not method:
        await query.edit_message_text("⚠️ طريقة السحب غير موجودة.")
        return

    if user["available"] < method["min_amount"]:
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]]
        await query.edit_message_text(
            f"⚠️ رصيدك ({user['available']}) أقل من الحد الأدنى لـ {method_name} ({method['min_amount']} وحدة).",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    context.user_data["withdraw_method"] = method_name
    await query.edit_message_text(f"📝 أرسل بيانات السحب لطريقة {method_name}:")


# ==================== WITHDRAWAL HISTORY ====================
async def withdrawal_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    withdrawals = db.get_user_withdrawals(user_id)

    if not withdrawals:
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]]
        await query.edit_message_text("📜 لا يوجد سجل سحوبات.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    status_map = {"pending": "⏳ قيد المراجعة", "approved": "✅ مقبول", "rejected": "❌ مرفوض"}
    msg = "📜 سجل السحوبات:\n\n"
    for w in withdrawals[:15]:
        s = status_map.get(w["status"], w["status"])
        msg += f"#{w['id']} | {w['method']} | {w['amount']} وحدة | {s}\n"

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== REFERRALS ====================
async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = db.get_user(user_id)

    ref_count = db.get_referral_count(user_id)
    ref_tasks = db.get_referral_completed_tasks(user_id)
    ref_reward = int(db.get_setting("referral_reward") or 2)
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    keyboard = [
        [InlineKeyboardButton("🏆 تصنيف الإحالات", callback_data="leaderboard")],
        [InlineKeyboardButton("💸 سحب رصيد الإحالات", callback_data="withdraw_referral")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")],
    ]

    msg = (
        f"👥 الإحالات\n\n"
        f"🔗 رابط الدعوة الخاص بك:\n{invite_link}\n\n"
        f"👤 عدد الإحالات: {ref_count}\n"
        f"📋 مهام المُحالين المكتملة: {ref_tasks}\n"
        f"💰 رصيد الإحالات: {user['referral_balance']} وحدة\n"
        f"🎁 مكافأة لكل مهمة يعملها المُحال: {ref_reward} وحدة"
    )
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lb = db.get_leaderboard()
    min_refs = int(db.get_setting("leaderboard_min_referrals") or 10)
    min_tasks = int(db.get_setting("leaderboard_min_tasks") or 20)

    msg = f"🏆 تصنيف الإحالات\n(الحد الأدنى: {min_refs} إحالة و {min_tasks} مهمة)\n\n"

    rank = 1
    for entry in lb[:10]:
        if entry["ref_count"] >= min_refs and entry["task_count"] >= min_tasks:
            msg += f"{rank}. {entry['username'] or entry['referrer_id']} - {entry['ref_count']} إحالة\n"
            rank += 1

    if rank == 1:
        msg += "لا يوجد مشاركين مؤهلين حالياً."

    keyboard = [[InlineKeyboardButton("🔙 الإحالات", callback_data="referrals")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def withdraw_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = db.get_user(user_id)

    if not user or user["referral_balance"] <= 0:
        await query.answer("⚠️ رصيد الإحالات فارغ!", show_alert=True)
        return

    # Move referral balance to available
    amount = user["referral_balance"]
    db.add_to_available(user_id, amount)
    db.update_user_balance(user_id, referral_balance=0)

    await query.edit_message_text(
        f"✅ تم تحويل {amount} وحدة من رصيد الإحالات إلى الرصيد المتاح.\n"
        f"يمكنك سحبه من قائمة سحب الأرباح.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]])
    )


# ==================== HELP ====================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = (
        "ℹ️ المساعدة\n\n"
        "📋 طلب مهمة: اطلب مهمة جديدة لإنشاء حساب إيميل\n"
        "💰 رصيدي: عرض رصيدك الحالي\n"
        "📊 مهامي: عرض قائمة مهامك\n"
        "💸 سحب الأرباح: طلب سحب الأرباح\n"
        "👥 الإحالات: عرض رابط الإحالة الخاص بك\n"
        "🎬 طريقة عمل المهمة: شاهد فيديو توضيحي\n\n"
        "💡 كيف يعمل النظام:\n"
        "1. اطلب مهمة جديدة\n"
        "2. ستحصل على بيانات حساب لإنشائه\n"
        "3. أنشئ الحساب وأرسل الإثبات\n"
        "4. بعد الموافقة تحصل على المكافأة\n\n"
        "📞 للدعم الفني: @gmailfarmermaxsupport"
    )
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== TUTORIAL ====================
async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_id = db.get_setting("tutorial_video_id")
    if video_id:
        await context.bot.send_video(query.from_user.id, video_id, caption="🎬 فيديو شرح طريقة عمل المهمة")
    else:
        await context.bot.send_message(query.from_user.id, "⚠️ لم يتم تحديد فيديو الشرح بعد.")
