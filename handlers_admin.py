from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db
from config import ADMIN_ID
from helpers import is_admin, send_to_admins


# ==================== ADMIN PANEL ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("📋 المهام المعلقة", callback_data="admin_pending_tasks"),
         InlineKeyboardButton("💸 طلبات السحب", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users"),
         InlineKeyboardButton("🔒 الرصيد المحجوز", callback_data="admin_reserved")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings"),
         InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="admin_search_user")],
        [InlineKeyboardButton("🗑️ مسح رصيد مستخدم", callback_data="admin_clear_balance"),
         InlineKeyboardButton("❌ إلغاء مهمة", callback_data="admin_cancel_task")],
        [InlineKeyboardButton("🎁 المكافأة", callback_data="admin_reward_user"),
         InlineKeyboardButton("🚫 حظر/رفع حظر", callback_data="admin_ban_user")],
        [InlineKeyboardButton("👮 إدارة المشرفين", callback_data="admin_manage_admins"),
         InlineKeyboardButton("🎬 فيديو الشرح", callback_data="admin_set_video")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_menu")],
    ]
    await query.edit_message_text("🔧 لوحة الإدارة:", reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== PENDING TASKS ====================
async def admin_pending_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    tasks = db.get_pending_tasks()
    if not tasks:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("✅ لا توجد مهام معلقة.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    status_map = {
        "pending": "⏳ بانتظار البيانات",
        "proof_submitted": "📸 إثبات مرسل",
        "error_resubmitted": "📸 إثبات معاد",
    }

    msg = "📋 المهام المعلقة:\n\n"
    for t in tasks[:20]:
        s = status_map.get(t["status"], t["status"])
        msg += f"#{t['id']} | مستخدم: {t['user_id']} | {s}\n"

    keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== ADMIN WITHDRAWALS ====================
async def admin_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    withdrawals = db.get_pending_withdrawals()
    if not withdrawals:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("✅ لا توجد طلبات سحب معلقة.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    msg = "💸 طلبات السحب المعلقة:\n\n"
    for w in withdrawals[:20]:
        msg += f"#{w['id']} | مستخدم: {w['user_id']} | {w['method']} | {w['amount']} جنيه\n"
        keyboard_w = [
            [InlineKeyboardButton("✅ قبول", callback_data=f"admin_approve_w_{w['id']}"),
             InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_w_{w['id']}")]
        ]
        # Send individual messages for each withdrawal
    # For now show list
    keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    # Send individual withdrawal cards
    for w in withdrawals[:10]:
        kb = [
            [InlineKeyboardButton("✅ قبول", callback_data=f"admin_approve_w_{w['id']}"),
             InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_w_{w['id']}")]
        ]
        await context.bot.send_message(
            query.from_user.id,
            f"💸 طلب سحب #{w['id']}\n"
            f"👤 مستخدم: {w['user_id']}\n"
            f"📱 الطريقة: {w['method']}\n"
            f"📝 البيانات: {w['data']}\n"
            f"💰 المبلغ: {w['amount']} جنيه",
            reply_markup=InlineKeyboardMarkup(kb)
        )


async def admin_approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer()
        return

    wid = int(query.data.split("_")[-1])
    context.user_data["admin_approve_withdrawal_id"] = wid
    await query.answer("✅ تم قبول الطلب، أرسل الآن صورة الإيصال", show_alert=True)
    await query.edit_message_text(f"📸 أرسل سكرين شوت إثبات السحب #{wid}:")


async def admin_reject_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer()
        return

    wid = int(query.data.split("_")[-1])
    w = db.get_withdrawal(wid)
    db.reject_withdrawal(wid)
    
    if w:
        try:
            await context.bot.send_message(w["user_id"], f"❌ تم رفض طلب السحب #{wid}.\nتم إرجاع الرصيد لحسابك.")
            await query.answer(
                f"❌ تم رفض طلب السحب\n"
                f"🆔 الطلب: #{wid}\n"
                f"👤 المستخدم: {w['user_id']}\n"
                f"💰 المبلغ: {w['amount']} جنيه",
                show_alert=True
            )
        except Exception as e:
            await query.answer(f"❌ تم الرفض لكن تعذر إرسال الإشعار: {str(e)}", show_alert=True)
    else:
        await query.answer("❌ تم رفض الطلب", show_alert=True)
    
    await query.edit_message_text(
        f"❌ تم رفض طلب السحب بنجاح\n"
        f"🆔 الطلب: #{wid}\n"
        f"👤 المستخدم: {w['user_id'] if w else 'غير معروف'}\n"
        f"تم إرجاع الرصيد للمستخدم."
    )


# ==================== ADMIN USERS ====================
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    total = db.get_user_count()
    active = db.get_active_user_count()
    balances = db.get_total_balances()

    keyboard = [
        [InlineKeyboardButton("📋 بيانات المستخدمين", callback_data="admin_users_list")],
        [InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")],
    ]

    msg = (
        f"👥 إدارة المستخدمين\n\n"
        f"📊 إجمالي المستخدمين: {total}\n"
        f"🟢 المستخدمين النشطين: {active}\n"
        f"💰 إجمالي الرصيد المتاح: {balances['avail']} جنيه\n"
        f"🔒 إجمالي الرصيد المحجوز: {balances['res']} جنيه\n"
        f"👥 إجمالي رصيد الإحالات: {balances['ref']} جنيه"
    )
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    users = db.get_all_users()
    msg = "📋 بيانات المستخدمين:\n\n"
    for u in users[:30]:
        ref_count = db.get_referral_count(u["id"])
        
        # Build display name
        display_name = ""
        if u.get('first_name'):
            display_name = u['first_name']
            if u.get('last_name'):
                display_name += f" {u['last_name']}"
        
        username_display = f"@{u['username']}" if u.get('username') else "لا يوجد"
        
        msg += (
            f"👤 {display_name or 'غير معروف'}\n"
            f"🆔 ID: {u['id']} | 📱 {username_display}\n"
            f"💰 متاح: {u['available']} | 🔒 محجوز: {u['reserved']} | 👥 إحالات: {u['referral_balance']} | عدد: {ref_count}\n\n"
        )

    if len(msg) > 4000:
        msg = msg[:4000] + "\n... (تم اقتطاع القائمة)"

    keyboard = [[InlineKeyboardButton("🔙 إدارة المستخدمين", callback_data="admin_users")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== ADMIN RESERVED ====================
async def admin_reserved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    tasks = db.get_reserved_tasks()
    if not tasks:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("✅ لا يوجد رصيد محجوز.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    msg = "🔒 المهام ذات الرصيد المحجوز:\n\n"
    for t in tasks[:20]:
        msg += f"#{t['id']} | مستخدم: {t['user_id']} | {t['price']} جنيه | حتى: {t['reserved_until']}\n"

    # Check if any are ready to release
    ready = db.get_tasks_ready_to_release()
    if ready:
        msg += f"\n⏰ {len(ready)} مهمة جاهزة للتحويل للرصيد المتاح.\n"
        for t in ready:
            kb = [[InlineKeyboardButton("✅ تحويل للمتاح", callback_data=f"admin_release_{t['id']}")]]
            await context.bot.send_message(
                query.from_user.id,
                f"⏰ المهمة #{t['id']} جاهزة للتحويل\n"
                f"👤 مستخدم: {t['user_id']}\n"
                f"💰 المبلغ: {t['price']} جنيه\n"
                f"هل تريد تحويل الرصيد للمتاح؟",
                reply_markup=InlineKeyboardMarkup(kb)
            )

    keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_release_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    task_id = int(query.data.split("_")[-1])
    task = db.get_task(task_id)
    if not task or task["status"] != "approved":
        await query.edit_message_text("⚠️ المهمة غير موجودة أو تم تحويلها بالفعل.")
        return

    db.release_task(task_id)
    db.move_reserved_to_available(task["user_id"], task["price"])

    await query.edit_message_text(f"✅ تم تحويل {task['price']} جنيه للرصيد المتاح للمستخدم {task['user_id']}.")
    await context.bot.send_message(task["user_id"],
        f"✅ تم تحويل {task['price']} جنيه من الرصيد المحجوز إلى الرصيد المتاح!"
    )


# ==================== ADMIN SETTINGS ====================
async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    task_price = db.get_setting("task_price")
    ref_reward = db.get_setting("referral_reward")
    min_w = db.get_setting("min_withdrawal")
    bot_active = db.get_setting("bot_active")
    methods = db.get_withdrawal_methods()

    msg = (
        f"⚙️ الإعدادات الحالية:\n\n"
        f"💰 سعر المهمة: {task_price} جنيه\n"
        f"👥 مكافأة الإحالة: {ref_reward} جنيه\n"
        f"💸 الحد الأدنى للسحب: {min_w} جنيه\n"
        f"🤖 حالة البوت: {'🟢 نشط' if bot_active == '1' else '🔴 متوقف'}\n\n"
        f"📱 طرق السحب:\n"
    )
    for m in methods:
        msg += f"  - {m['name']}: حد أدنى {m['min_amount']} | رسوم {m['fee']}\n"

    keyboard = [
        [InlineKeyboardButton("💰 تغيير سعر المهمة", callback_data="admin_set_task_price"),
         InlineKeyboardButton("👥 مكافأة الإحالة", callback_data="admin_set_ref_reward")],
        [InlineKeyboardButton("💸 الحد الأدنى للسحب", callback_data="admin_set_min_w"),
         InlineKeyboardButton("📱 رسوم طرق السحب", callback_data="admin_set_fees")],
        [InlineKeyboardButton("➕ إضافة طريقة سحب", callback_data="admin_add_method"),
         InlineKeyboardButton(
            "🔴 إيقاف البوت" if bot_active == "1" else "🟢 تشغيل البوت",
            callback_data="admin_toggle_bot"
        )],
        [InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")],
    ]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    current = db.get_setting("bot_active")
    new_val = "0" if current == "1" else "1"
    db.set_setting("bot_active", new_val)
    status = "🟢 نشط" if new_val == "1" else "🔴 متوقف"
    await query.answer(f"تم تغيير حالة البوت إلى: {status}", show_alert=True)
    # Refresh settings page
    await admin_settings(update, context)


async def admin_set_task_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("5 جنيه", callback_data="admin_price_5"),
         InlineKeyboardButton("10 جنيه", callback_data="admin_price_10")],
        [InlineKeyboardButton("15 جنيه", callback_data="admin_price_15"),
         InlineKeyboardButton("20 جنيه", callback_data="admin_price_20")],
        [InlineKeyboardButton("25 جنيه", callback_data="admin_price_25"),
         InlineKeyboardButton("30 جنيه", callback_data="admin_price_30")],
        [InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")]
    ]
    await query.edit_message_text("💰 اختر سعر المهمة الجديد:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_price_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    price = int(query.data.split("_")[-1])
    db.set_setting("task_price", str(price))
    await query.answer(f"✅ تم تغيير سعر المهمة إلى {price} جنيه", show_alert=True)
    await admin_settings(update, context)


async def admin_set_ref_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("1 جنيه", callback_data="admin_ref_1"),
         InlineKeyboardButton("2 جنيه", callback_data="admin_ref_2")],
        [InlineKeyboardButton("3 جنيه", callback_data="admin_ref_3"),
         InlineKeyboardButton("5 جنيه", callback_data="admin_ref_5")],
        [InlineKeyboardButton("10 جنيه", callback_data="admin_ref_10"),
         InlineKeyboardButton("15 جنيه", callback_data="admin_ref_15")],
        [InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")]
    ]
    await query.edit_message_text("👥 اختر مكافأة الإحالة الجديدة:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_ref_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    reward = int(query.data.split("_")[-1])
    db.set_setting("referral_reward", str(reward))
    await query.answer(f"✅ تم تغيير مكافأة الإحالة إلى {reward} جنيه", show_alert=True)
    await admin_settings(update, context)


async def admin_set_min_w(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("20 جنيه", callback_data="admin_minw_20"),
         InlineKeyboardButton("30 جنيه", callback_data="admin_minw_30")],
        [InlineKeyboardButton("50 جنيه", callback_data="admin_minw_50"),
         InlineKeyboardButton("100 جنيه", callback_data="admin_minw_100")],
        [InlineKeyboardButton("150 جنيه", callback_data="admin_minw_150"),
         InlineKeyboardButton("200 جنيه", callback_data="admin_minw_200")],
        [InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")]
    ]
    await query.edit_message_text("💸 اختر الحد الأدنى للسحب الجديد:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_minw_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    min_w = int(query.data.split("_")[-1])
    db.set_setting("min_withdrawal", str(min_w))
    await query.answer(f"✅ تم تغيير الحد الأدنى للسحب إلى {min_w} جنيه", show_alert=True)
    await admin_settings(update, context)


async def admin_set_fees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    methods = db.get_withdrawal_methods()
    keyboard = []
    for m in methods:
        keyboard.append([InlineKeyboardButton(
            f"{m['name']} (رسوم: {m['fee']} | حد: {m['min_amount']})",
            callback_data=f"admin_edit_method_{m['name']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")])
    await query.edit_message_text("📱 اختر طريقة السحب لتعديلها:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_edit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    method_name = query.data.replace("admin_edit_method_", "")
    keyboard = [
        [InlineKeyboardButton("💰 تغيير الحد الأدنى", callback_data=f"admin_method_min_{method_name}")],
        [InlineKeyboardButton("📊 تغيير الرسوم", callback_data=f"admin_method_fee_{method_name}")],
        [InlineKeyboardButton("🔙 طرق السحب", callback_data="admin_set_fees")],
    ]
    await query.edit_message_text(f"تعديل طريقة: {method_name}", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_method_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    method_name = query.data.replace("admin_method_min_", "")
    
    keyboard = [
        [InlineKeyboardButton("20 جنيه", callback_data=f"admin_setmin_{method_name}_20"),
         InlineKeyboardButton("30 جنيه", callback_data=f"admin_setmin_{method_name}_30")],
        [InlineKeyboardButton("50 جنيه", callback_data=f"admin_setmin_{method_name}_50"),
         InlineKeyboardButton("100 جنيه", callback_data=f"admin_setmin_{method_name}_100")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_edit_method_{method_name}")]
    ]
    await query.edit_message_text(f"اختر الحد الأدنى لـ {method_name}:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_method_min_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    parts = query.data.split("_")
    method_name = parts[2]
    value = int(parts[3])
    
    db.update_withdrawal_method_min(method_name, value)
    await query.answer(f"✅ تم تغيير الحد الأدنى إلى {value} جنيه", show_alert=True)
    await query.edit_message_text(f"✅ تم تغيير الحد الأدنى لـ {method_name} إلى {value} جنيه")


async def admin_method_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    method_name = query.data.replace("admin_method_fee_", "")
    
    keyboard = [
        [InlineKeyboardButton("0 جنيه", callback_data=f"admin_setfee_{method_name}_0"),
         InlineKeyboardButton("5 جنيه", callback_data=f"admin_setfee_{method_name}_5")],
        [InlineKeyboardButton("10 جنيه", callback_data=f"admin_setfee_{method_name}_10"),
         InlineKeyboardButton("15 جنيه", callback_data=f"admin_setfee_{method_name}_15")],
        [InlineKeyboardButton("20 جنيه", callback_data=f"admin_setfee_{method_name}_20"),
         InlineKeyboardButton("25 جنيه", callback_data=f"admin_setfee_{method_name}_25")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_edit_method_{method_name}")]
    ]
    await query.edit_message_text(f"اختر الرسوم لـ {method_name}:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_method_fee_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    parts = query.data.split("_")
    method_name = parts[2]
    value = int(parts[3])
    
    db.update_withdrawal_method_fee(method_name, value)
    await query.answer(f"✅ تم تغيير الرسوم إلى {value} جنيه", show_alert=True)
    await query.edit_message_text(f"✅ تم تغيير رسوم {method_name} إلى {value} جنيه")


async def admin_add_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data["admin_adding_method"] = True
    await query.edit_message_text("📱 أرسل اسم طريقة السحب الجديدة:")


# ==================== ADMIN SEARCH USER ====================
async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Get all users and show as buttons
    users = db.get_all_users()
    if not users:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("لا يوجد مستخدمين.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = []
    for u in users[:30]:  # Show first 30 users
        # Build display name
        display_name = ""
        if u.get('first_name'):
            display_name = u['first_name']
            if u.get('last_name'):
                display_name += f" {u['last_name']}"
        
        username_display = f"@{u['username']}" if u.get('username') else ""
        button_text = f"👤 {display_name or 'غير معروف'} {username_display} (ID: {u['id']})"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"admin_view_user_{u['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
    
    await query.edit_message_text("👥 اختر مستخدم:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_view_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    user_id = int(query.data.split("_")[-1])
    user = db.get_user(user_id)
    if user:
        ref_count = db.get_referral_count(user_id)
        stats = db.get_user_task_stats(user_id)
        
        # Build display name
        display_name = ""
        if user.get('first_name'):
            display_name = user['first_name']
            if user.get('last_name'):
                display_name += f" {user['last_name']}"
        
        username_display = f"@{user['username']}" if user.get('username') else "لا يوجد"
        
        msg = (
            f"بيانات المستخدم:\n\n"
            f"👤 الاسم: {display_name or 'غير معروف'}\n"
            f"📱 اليوزر: {username_display}\n"
            f"🆔 ID: {user['id']}\n"
            f"💰 رصيد متاح: {user['available']}\n"
            f"🔒 رصيد محجوز: {user['reserved']}\n"
            f"👥 رصيد إحالات: {user['referral_balance']}\n"
            f"📋 إجمالي المهام: {stats['total']}\n"
            f"✅ مهام مقبولة: {stats['approved']}\n"
            f"❌ مهام مرفوضة: {stats['rejected']}\n"
            f"🔗 عدد الإحالات: {ref_count}"
        )
        keyboard = [[InlineKeyboardButton("🔙 قائمة المستخدمين", callback_data="admin_search_user")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("المستخدم غير موجود.")


# ==================== ADMIN CLEAR BALANCE ====================
async def admin_clear_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Get all users and show as buttons
    users = db.get_all_users()
    if not users:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("لا يوجد مستخدمين.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = []
    for u in users[:30]:
        total = u['available'] + u['reserved'] + u['referral_balance']
        if total > 0:  # Only show users with balance
            # Build display name
            display_name = ""
            if u.get('first_name'):
                display_name = u['first_name']
                if u.get('last_name'):
                    display_name += f" {u['last_name']}"
            
            username_display = f"@{u['username']}" if u.get('username') else ""
            button_text = f"🗑️ {display_name or 'غير معروف'} {username_display} - {total} جنيه"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"admin_do_clear_{u['id']}"
            )])
    
    if not keyboard:
        keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
        await query.edit_message_text("لا يوجد مستخدمين برصيد.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
    await query.edit_message_text("🗑️ اختر مستخدم لمسح رصيده:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_do_clear_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    user_id = int(query.data.split("_")[-1])
    user = db.get_user(user_id)
    if user:
        db.clear_user_balance(user_id)
        await query.answer(f"✅ تم مسح الرصيد\n👤 المستخدم: {user_id}", show_alert=True)
        await query.edit_message_text(f"✅ تم مسح رصيد المستخدم بالكامل\n👤 {user['username'] or user_id} (ID: {user_id})")
    else:
        await query.answer("❌ المستخدم غير موجود", show_alert=True)


# ==================== ADMIN CANCEL TASK ====================
async def admin_cancel_task_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Get incomplete tasks
    tasks = db.get_incomplete_tasks()
    if not tasks:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("✅ لا توجد مهام غير مكتملة.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    msg = "❌ المهام الغير مكتملة:\n\n"
    keyboard = []
    for t in tasks[:15]:
        status_map = {
            "pending": "⏳ معلقة",
            "data_sent": "📤 بيانات مرسلة",
            "proof_submitted": "📸 إثبات مرسل",
            "error": "⚠️ خطأ",
            "error_resubmitted": "📸 إثبات معاد",
        }
        status = status_map.get(t["status"], t["status"])
        msg += f"#{t['id']} | مستخدم: {t['user_id']} | {status}\n"
        keyboard.append([InlineKeyboardButton(f"❌ إلغاء المهمة #{t['id']}", callback_data=f"admin_do_cancel_{t['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== ADMIN MANAGE ADMINS ====================
async def admin_manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    admins = db.get_admins()
    msg = f"👮 المشرفين الحاليين:\n🆔 {ADMIN_ID} (المشرف الرئيسي)\n"
    for a in admins:
        if a != ADMIN_ID:
            msg += f"🆔 {a}\n"

    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف", callback_data="admin_add_admin"),
         InlineKeyboardButton("➖ إزالة مشرف", callback_data="admin_remove_admin")],
        [InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")],
    ]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data["admin_adding_admin"] = True
    await query.edit_message_text("➕ أرسل ID المشرف الجديد:")


async def admin_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data["admin_removing_admin"] = True
    await query.edit_message_text("➖ أرسل ID المشرف لإزالته:")


# ==================== ADMIN SET VIDEO ====================
async def admin_set_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data["admin_setting_video"] = True
    await query.edit_message_text("🎬 أرسل فيديو الشرح الآن:")



# ==================== ADMIN DO CANCEL TASK ====================
async def admin_do_cancel_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    task_id = int(query.data.split("_")[-1])
    task = db.get_task(task_id)
    if task:
        db.cancel_task(task_id)
        try:
            await context.bot.send_message(task["user_id"], f"❌ تم إلغاء المهمة #{task_id} بواسطة المشرف.")
            await query.answer(f"✅ تم إلغاء المهمة\n🆔 المهمة: #{task_id}\n👤 المستخدم: {task['user_id']}", show_alert=True)
        except Exception as e:
            await query.answer(f"✅ تم إلغاء المهمة #{task_id}\n⚠️ لكن تعذر إرسال الإشعار", show_alert=True)
        await query.edit_message_text(f"✅ تم إلغاء المهمة #{task_id} للمستخدم {task['user_id']}")
    else:
        await query.answer("⚠️ المهمة غير موجودة", show_alert=True)
        await query.edit_message_text("⚠️ المهمة غير موجودة.")


# ==================== ADMIN REWARD USER ====================
async def admin_reward_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Get all users and show as buttons
    users = db.get_all_users()
    if not users:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("لا يوجد مستخدمين.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = []
    for u in users[:30]:
        # Build display name
        display_name = ""
        if u.get('first_name'):
            display_name = u['first_name']
            if u.get('last_name'):
                display_name += f" {u['last_name']}"
        
        username_display = f"@{u['username']}" if u.get('username') else ""
        button_text = f"🎁 {display_name or 'غير معروف'} {username_display} (رصيد: {u['available']})"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"admin_reward_select_{u['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
    
    await query.edit_message_text("🎁 اختر مستخدم لإضافة مكافأة:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_reward_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    user_id = int(query.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await query.answer("المستخدم غير موجود", show_alert=True)
        return
    
    # Show amount buttons
    keyboard = [
        [InlineKeyboardButton("10 جنيه", callback_data=f"admin_reward_amount_{user_id}_10"),
         InlineKeyboardButton("20 جنيه", callback_data=f"admin_reward_amount_{user_id}_20")],
        [InlineKeyboardButton("50 جنيه", callback_data=f"admin_reward_amount_{user_id}_50"),
         InlineKeyboardButton("100 جنيه", callback_data=f"admin_reward_amount_{user_id}_100")],
        [InlineKeyboardButton("200 جنيه", callback_data=f"admin_reward_amount_{user_id}_200"),
         InlineKeyboardButton("500 جنيه", callback_data=f"admin_reward_amount_{user_id}_500")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_reward_user")]
    ]
    
    await query.edit_message_text(
        f"👤 المستخدم: {user['username'] or user_id}\n"
        f"💰 الرصيد الحالي: {user['available']} جنيه\n\n"
        f"اختر مبلغ المكافأة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_reward_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer()
        return
    
    parts = query.data.split("_")
    user_id = int(parts[-2])
    amount = int(parts[-1])
    
    db.add_to_available(user_id, amount)
    user = db.get_user(user_id)
    
    try:
        await context.bot.send_message(user_id, f"🎁 تم إضافة مكافأة {amount} جنيه لحسابك!")
        await query.answer(f"✅ تم إضافة المكافأة\n💰 {amount} جنيه للمستخدم {user_id}", show_alert=True)
    except Exception as e:
        await query.answer(f"✅ تم إضافة المكافأة\n💰 {amount} جنيه للمستخدم {user_id}\n⚠️ لكن تعذر إرسال الإشعار", show_alert=True)
    
    await query.edit_message_text(
        f"✅ تم إضافة المكافأة بنجاح\n"
        f"👤 المستخدم: {user['username'] or user_id} (ID: {user_id})\n"
        f"💰 المبلغ المضاف: {amount} جنيه\n"
        f"💵 الرصيد الجديد: {user['available']} جنيه"
    )


# ==================== ADMIN BAN USER ====================
async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Get all users and show as buttons
    users = db.get_all_users()
    if not users:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text("لا يوجد مستخدمين.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = []
    for u in users[:30]:
        is_banned = db.is_user_banned(u['id'])
        status = "🚫 محظور" if is_banned else "✅ نشط"
        action = "رفع الحظر" if is_banned else "حظر"
        
        # Build display name
        display_name = ""
        if u.get('first_name'):
            display_name = u['first_name']
            if u.get('last_name'):
                display_name += f" {u['last_name']}"
        
        username_display = f"@{u['username']}" if u.get('username') else ""
        button_text = f"{status} {display_name or 'غير معروف'} {username_display} - {action}"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"admin_do_ban_{u['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
    
    await query.edit_message_text("🚫 اختر مستخدم للحظر/رفع الحظر:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_do_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    user_id = int(query.data.split("_")[-1])
    user = db.get_user(user_id)
    if not user:
        await query.answer("المستخدم غير موجود", show_alert=True)
        return
    
    if db.is_user_banned(user_id):
        db.unban_user(user_id)
        try:
            await context.bot.send_message(user_id, "✅ تم رفع الحظر عنك. يمكنك استخدام البوت الآن.")
            await query.answer(f"✅ تم رفع الحظر\n👤 المستخدم: {user_id}", show_alert=True)
        except Exception:
            await query.answer(f"✅ تم رفع الحظر\n👤 المستخدم: {user_id}\n⚠️ لكن تعذر إرسال الإشعار", show_alert=True)
        await query.edit_message_text(f"✅ تم رفع الحظر عن المستخدم\n👤 {user['username'] or user_id} (ID: {user_id})")
    else:
        db.ban_user(user_id)
        try:
            await context.bot.send_message(user_id, "⛔ تم حظرك من استخدام البوت.")
            await query.answer(f"🚫 تم حظر المستخدم\n👤 المستخدم: {user_id}", show_alert=True)
        except Exception:
            await query.answer(f"🚫 تم حظر المستخدم\n👤 المستخدم: {user_id}\n⚠️ لكن تعذر إرسال الإشعار", show_alert=True)
        await query.edit_message_text(f"🚫 تم حظر المستخدم\n👤 {user['username'] or user_id} (ID: {user_id})")


# ==================== ADMIN TOGGLE BOT WITH NOTIFICATION ====================
async def admin_toggle_bot_with_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    current = db.get_setting("bot_active")
    new_val = "0" if current == "1" else "1"
    db.set_setting("bot_active", new_val)
    status = "🟢 نشط" if new_val == "1" else "🔴 متوقف"
    
    # Send notification to all users
    user_ids = db.get_all_user_ids()
    if new_val == "1":
        msg = "🟢 البوت الآن نشط! يمكنك طلب المهام."
    else:
        msg = "🔴 البوت متوقف مؤقتاً. سيتم إعلامك عند التشغيل."
    
    sent_count = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(uid, msg)
            sent_count += 1
        except Exception:
            pass
    
    await query.answer(f"تم تغيير حالة البوت إلى: {status}\nتم إرسال الإشعار لـ {sent_count} مستخدم", show_alert=True)
    # Refresh settings page
    await admin_settings(update, context)
