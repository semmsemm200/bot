from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db
from config import ADMIN_ID
from helpers import is_admin, send_to_admins


# Helper function to get user display name
def get_user_display_name(user):
    """Get user display name from user dict, handling missing columns"""
    try:
        # Convert Row to dict if needed
        if hasattr(user, 'keys'):
            user_dict = dict(user)
        else:
            user_dict = user
            
        # Try to get username first (this column always exists)
        username = user_dict.get('username', None) if isinstance(user_dict, dict) else user['username']
        user_id = user_dict.get('id', 'غير معروف') if isinstance(user_dict, dict) else user['id']
        
        # Return username or ID
        return username if username else str(user_id)
    except Exception:
        return "غير معروف"


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

    try:
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
    except Exception as e:
        keyboard = [[InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")]]
        await query.edit_message_text(f"⚠️ خطأ في قراءة البيانات: {str(e)}", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    try:
        users = db.get_all_users()
        
        # Debug: check if users is None or empty
        if users is None:
            keyboard = [[InlineKeyboardButton("🔙 إدارة المستخدمين", callback_data="admin_users")]]
            await query.edit_message_text("⚠️ خطأ: لم يتم إرجاع بيانات من قاعدة البيانات.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        if not users or len(users) == 0:
            keyboard = [[InlineKeyboardButton("🔙 إدارة المستخدمين", callback_data="admin_users")]]
            await query.edit_message_text("لا يوجد مستخدمين مسجلين في البوت.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        msg = f"📋 بيانات المستخدمين ({len(users)} مستخدم):\n\n"
        for u in users[:30]:
            try:
                # Convert sqlite3.Row to dict
                user_dict = dict(u)
                
                user_id = user_dict.get('id', 0)
                username = user_dict.get('username', None)
                available = user_dict.get('available', 0)
                reserved = user_dict.get('reserved', 0)
                referral_balance = user_dict.get('referral_balance', 0)
                
                ref_count = db.get_referral_count(user_id)
                display_name = username if username else str(user_id)
                username_display = f"@{username}" if username else "لا يوجد"
                
                msg += (
                    f"👤 {display_name}\n"
                    f"🆔 ID: {user_id} | 📱 {username_display}\n"
                    f"💰 متاح: {available} | 🔒 محجوز: {reserved} | 👥 إحالات: {referral_balance} | عدد: {ref_count}\n\n"
                )
            except Exception as e:
                msg += f"⚠️ خطأ في قراءة مستخدم: {str(e)}\n\n"
                continue

        if len(msg) > 4000:
            msg = msg[:4000] + "\n... (تم اقتطاع القائمة)"

        keyboard = [[InlineKeyboardButton("🔙 إدارة المستخدمين", callback_data="admin_users")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        keyboard = [[InlineKeyboardButton("🔙 إدارة المستخدمين", callback_data="admin_users")]]
        await query.edit_message_text(f"⚠️ حدث خطأ في قراءة البيانات: {str(e)}", reply_markup=InlineKeyboardMarkup(keyboard))


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

    # Group tasks by user_id
    users_tasks = {}
    for t in tasks:
        user_id = t['user_id']
        if user_id not in users_tasks:
            users_tasks[user_id] = []
        users_tasks[user_id].append(t)
    
    # Create user list with task counts
    msg = f"🔒 الرصيد المحجوز ({len(tasks)} مهمة من {len(users_tasks)} مستخدم):\n\n"
    keyboard = []
    
    for user_id, user_tasks in users_tasks.items():
        user = db.get_user(user_id)
        user_dict = dict(user) if user else {}
        username = user_dict.get('username', None) if user else None
        display_name = f"@{username}" if username else f"ID: {user_id}"
        
        total_amount = sum(t['price'] for t in user_tasks)
        task_count = len(user_tasks)
        
        keyboard.append([InlineKeyboardButton(
            f"👤 {display_name} - {task_count} مهمة ({total_amount} جنيه)",
            callback_data=f"admin_reserved_user_{user_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin_panel")])
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_reserved_user_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    user_id = int(query.data.split("_")[-1])
    tasks = db.get_reserved_tasks_by_user(user_id)
    
    if not tasks:
        keyboard = [[InlineKeyboardButton("🔙 قائمة المستخدمين", callback_data="admin_reserved")]]
        await query.edit_message_text(
            "⚠️ لا توجد مهام محجوزة لهذا المستخدم",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    from datetime import datetime
    
    user = db.get_user(user_id)
    user_dict = dict(user) if user else {}
    username = user_dict.get('username', None) if user else None
    display_name = f"@{username}" if username else f"ID: {user_id}"
    
    msg = f"🔒 المهام المحجوزة للمستخدم {display_name}\n\n"
    
    keyboard = []
    for t in tasks:
        try:
            # Convert task to dict if needed
            task_dict = dict(t) if hasattr(t, 'keys') else t
            task_id = task_dict.get('id', 0)
            price = task_dict.get('price', 0)
            completed_at_str = task_dict.get('completed_at')
            reserved_until_str = task_dict.get('reserved_until')
            
            # Calculate time passed since approval
            time_info = "⏱️ غير محدد"
            if completed_at_str:
                try:
                    # Handle both datetime objects and strings
                    if isinstance(completed_at_str, str):
                        # Remove timezone info if present for parsing
                        completed_at_str = completed_at_str.replace('+00:00', '').replace('Z', '').split('.')[0]
                        completed_at = datetime.fromisoformat(completed_at_str)
                    else:
                        completed_at = completed_at_str
                    
                    now = datetime.now()
                    time_passed = now - completed_at
                    hours_passed = int(time_passed.total_seconds() // 3600)
                    minutes_passed = int((time_passed.total_seconds() % 3600) // 60)
                    time_info = f"⏱️ مر {hours_passed} ساعة و {minutes_passed} دقيقة"
                except Exception as e:
                    print(f"Error parsing completed_at for task {task_id}: {e}")
                    time_info = "⏱️ غير محدد"
            
            # Time remaining
            time_remaining = "✅ جاهز للتحرير"
            status_emoji = "🟢"
            if reserved_until_str:
                try:
                    # Handle both datetime objects and strings
                    if isinstance(reserved_until_str, str):
                        # Remove timezone info if present for parsing
                        reserved_until_str = reserved_until_str.replace('+00:00', '').replace('Z', '').split('.')[0]
                        reserved_until = datetime.fromisoformat(reserved_until_str)
                    else:
                        reserved_until = reserved_until_str
                    
                    now = datetime.now()
                    time_diff = reserved_until - now
                    
                    if time_diff.total_seconds() > 0:
                        hours_remaining = int(time_diff.total_seconds() // 3600)
                        minutes_remaining = int((time_diff.total_seconds() % 3600) // 60)
                        time_remaining = f"⏰ باقي {hours_remaining}س {minutes_remaining}د"
                        status_emoji = "🟡"
                except Exception as e:
                    print(f"Error parsing reserved_until for task {task_id}: {e}")
            
            msg += (
                f"{status_emoji} المهمة #{task_id}\n"
                f"💰 المبلغ: {price} جنيه\n"
                f"{time_info}\n"
                f"{time_remaining}\n\n"
            )
            
            keyboard.append([
                InlineKeyboardButton(f"📋 تفاصيل #{task_id}", callback_data=f"admin_task_details_{task_id}"),
                InlineKeyboardButton(f"✅ تحرير #{task_id}", callback_data=f"admin_release_{task_id}")
            ])
        except Exception as e:
            print(f"Error processing task: {e}")
            # Still try to show the task with minimal info
            try:
                task_dict = dict(t) if hasattr(t, 'keys') else t
                task_id = task_dict.get('id', 0)
                price = task_dict.get('price', 0)
                msg += f"⚠️ المهمة #{task_id} - {price} جنيه (خطأ في البيانات)\n\n"
                keyboard.append([
                    InlineKeyboardButton(f"✅ تحرير #{task_id}", callback_data=f"admin_release_{task_id}")
                ])
            except:
                continue
    
    # Add option to release all tasks for this user
    try:
        total_amount = sum(dict(t).get('price', 0) if hasattr(t, 'keys') else t.get('price', 0) for t in tasks)
        keyboard.append([InlineKeyboardButton(
            f"✅ تحرير الكل ({len(tasks)} مهمة - {total_amount} جنيه)",
            callback_data=f"admin_release_all_{user_id}"
        )])
    except:
        pass
    
    keyboard.append([InlineKeyboardButton("🔙 قائمة المستخدمين", callback_data="admin_reserved")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_release_all_user_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer()
        return

    user_id = int(query.data.split("_")[-1])
    tasks = db.get_reserved_tasks_by_user(user_id)
    
    if not tasks:
        await query.answer("⚠️ لا توجد مهام محجوزة لهذا المستخدم", show_alert=True)
        return
    
    released_count = 0
    total_amount = 0
    
    for t in tasks:
        try:
            db.move_reserved_to_available(t['user_id'], t['price'])
            db.release_task(t['id'])
            released_count += 1
            total_amount += t['price']
        except Exception:
            continue
    
    # Notify user
    try:
        await context.bot.send_message(
            user_id,
            f"✅ تم تحرير رصيدك المحجوز!\n"
            f"💰 المبلغ: {total_amount} جنيه\n"
            f"📋 عدد المهام: {released_count}\n\n"
            f"الرصيد أصبح متاحاً للسحب الآن."
        )
    except Exception:
        pass
    
    await query.answer(
        f"✅ تم تحرير {released_count} مهمة\n"
        f"💰 المبلغ: {total_amount} جنيه\n"
        f"👤 المستخدم: {user_id}",
        show_alert=True
    )
    
    # Go back to reserved list
    await admin_reserved(update, context)


async def admin_release_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer()
        return

    task_id = int(query.data.split("_")[-1])
    task = db.get_task(task_id)
    if not task or task["status"] != "approved":
        await query.answer("⚠️ المهمة غير موجودة أو تم تحويلها بالفعل", show_alert=True)
        return

    user_id = task["user_id"]
    
    try:
        db.release_task(task_id)
        db.move_reserved_to_available(user_id, task["price"])
        
        await query.answer(f"✅ تم تحرير الرصيد\n💰 {task['price']} جنيه", show_alert=True)
        
        # Notify user
        try:
            await context.bot.send_message(
                user_id,
                f"✅ تم تحويل {task['price']} جنيه من الرصيد المحجوز إلى الرصيد المتاح!"
            )
        except Exception:
            pass
        
        # Go back to user's tasks list
        query.data = f"admin_reserved_user_{user_id}"
        await admin_reserved_user_tasks(update, context)
    except Exception as e:
        await query.answer(f"❌ خطأ: {str(e)}", show_alert=True)
        # Still try to go back to the list
        query.data = f"admin_reserved_user_{user_id}"
        await admin_reserved_user_tasks(update, context)


async def admin_task_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    task_id = int(query.data.split("_")[-1])
    task = db.get_task(task_id)
    
    if not task:
        await query.edit_message_text("⚠️ المهمة غير موجودة.")
        return
    
    from datetime import datetime
    
    # Convert to dict
    task_dict = dict(task) if hasattr(task, 'keys') else task
    
    # Get user info
    user = db.get_user(task_dict['user_id'])
    user_dict = dict(user) if user else {}
    username = user_dict.get('username', None) if user else None
    display_name = username if username else str(task_dict['user_id'])
    
    # Calculate time
    time_status = "غير محدد"
    reserved_until_str = task_dict.get('reserved_until')
    if reserved_until_str:
        try:
            # Handle both datetime objects and strings
            if isinstance(reserved_until_str, str):
                # Remove timezone info if present for parsing
                reserved_until_str = reserved_until_str.replace('+00:00', '').replace('Z', '').split('.')[0]
                reserved_until = datetime.fromisoformat(reserved_until_str)
            else:
                reserved_until = reserved_until_str
            
            now = datetime.now()
            time_diff = reserved_until - now
            
            if time_diff.total_seconds() > 0:
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                time_status = f"⏰ باقي: {hours} ساعة و {minutes} دقيقة"
            else:
                time_status = "✅ جاهز للتحرير الآن"
        except Exception as e:
            print(f"Error parsing reserved_until in task_details: {e}")
            time_status = "✅ جاهز للتحرير الآن"
    
    # Build detailed message
    msg = (
        f"📋 تفاصيل المهمة #{task_id}\n\n"
        f"👤 المستخدم: {display_name}\n"
        f"🆔 ID: {task_dict['user_id']}\n"
        f"💰 المبلغ: {task_dict['price']} جنيه\n"
        f"📊 الحالة: {task_dict['status']}\n"
        f"{time_status}\n\n"
    )
    
    if task_dict.get('admin_data'):
        msg += f"📝 البيانات المرسلة:\n{task_dict['admin_data']}\n\n"
    
    if task_dict.get('created_at'):
        msg += f"📅 تاريخ الإنشاء: {task_dict['created_at']}\n"
    
    if task_dict.get('completed_at'):
        msg += f"✅ تاريخ الموافقة: {task_dict['completed_at']}\n"
    
    if task_dict.get('reserved_until'):
        msg += f"🔒 محجوز حتى: {task_dict['reserved_until']}\n"
    
    keyboard = [
        [InlineKeyboardButton("✅ تحرير الرصيد الآن", callback_data=f"admin_release_{task_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_reserved_user_{task_dict['user_id']}")]
    ]
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


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
        [InlineKeyboardButton("✏️ إدخال مخصص", callback_data="admin_price_custom")],
        [InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")]
    ]
    await query.edit_message_text("💰 اختر سعر المهمة الجديد:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_price_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Check if custom input
    if query.data == "admin_price_custom":
        context.user_data["admin_setting_task_price"] = True
        await query.edit_message_text("✏️ أرسل سعر المهمة الجديد (رقم فقط):")
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
        [InlineKeyboardButton("✏️ إدخال مخصص", callback_data="admin_ref_custom")],
        [InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")]
    ]
    await query.edit_message_text("👥 اختر مكافأة الإحالة الجديدة:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_ref_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    
    # Check if custom input
    if query.data == "admin_ref_custom":
        context.user_data["admin_setting_ref_reward"] = True
        await query.edit_message_text("✏️ أرسل مكافأة الإحالة الجديدة (رقم فقط):")
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
        [InlineKeyboardButton("✏️ إدخال مخصص", callback_data="admin_minw_custom")],
        [InlineKeyboardButton("🔙 الإعدادات", callback_data="admin_settings")]
    ]
    await query.edit_message_text("💸 اختر الحد الأدنى للسحب الجديد:", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_set_minw_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer()
        return
    
    # Check if custom input
    if query.data == "admin_minw_custom":
        context.user_data["admin_setting_min_withdrawal"] = True
        await query.answer()
        await query.edit_message_text("✏️ أرسل الحد الأدنى للسحب الجديد (رقم فقط):")
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
    if not is_admin(query.from_user.id):
        await query.answer()
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
    if not is_admin(query.from_user.id):
        await query.answer()
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
        # Convert sqlite3.Row to dict
        user_dict = dict(u)
        
        user_id = user_dict.get('id', 0)
        username = user_dict.get('username', None)
        display_name = username if username else str(user_id)
        username_display = f"@{username}" if username else ""
        button_text = f"👤 {display_name} {username_display} (ID: {user_id})"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"admin_view_user_{user_id}"
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
        # Convert sqlite3.Row to dict
        user_dict = dict(user)
        
        ref_count = db.get_referral_count(user_id)
        stats = db.get_user_task_stats(user_id)
        
        username = user_dict.get('username', None)
        display_name = username if username else str(user_id)
        username_display = f"@{username}" if username else "لا يوجد"
        
        msg = (
            f"بيانات المستخدم:\n\n"
            f"👤 الاسم: {display_name}\n"
            f"📱 اليوزر: {username_display}\n"
            f"🆔 ID: {user_dict['id']}\n"
            f"💰 رصيد متاح: {user_dict['available']}\n"
            f"🔒 رصيد محجوز: {user_dict['reserved']}\n"
            f"👥 رصيد إحالات: {user_dict['referral_balance']}\n"
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
        # Convert sqlite3.Row to dict
        user_dict = dict(u)
        
        user_id = user_dict.get('id', 0)
        username = user_dict.get('username', None)
        available = user_dict.get('available', 0)
        reserved = user_dict.get('reserved', 0)
        referral_balance = user_dict.get('referral_balance', 0)
        
        total = available + reserved + referral_balance
        if total > 0:  # Only show users with balance
            display_name = username if username else str(user_id)
            username_display = f"@{username}" if username else ""
            button_text = f"🗑️ {display_name} {username_display} - {total} جنيه"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"admin_do_clear_{user_id}"
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
        # Convert sqlite3.Row to dict
        user_dict = dict(u)
        
        user_id = user_dict.get('id', 0)
        username = user_dict.get('username', None)
        available = user_dict.get('available', 0)
        
        display_name = username if username else str(user_id)
        username_display = f"@{username}" if username else ""
        button_text = f"🎁 {display_name} {username_display} (رصيد: {available})"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"admin_reward_select_{user_id}"
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
        # Convert sqlite3.Row to dict
        user_dict = dict(u)
        
        user_id = user_dict.get('id', 0)
        username = user_dict.get('username', None)
        
        is_banned = db.is_user_banned(user_id)
        status = "🚫 محظور" if is_banned else "✅ نشط"
        action = "رفع الحظر" if is_banned else "حظر"
        
        display_name = username if username else str(user_id)
        username_display = f"@{username}" if username else ""
        button_text = f"{status} {display_name} {username_display} - {action}"
        
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"admin_do_ban_{user_id}"
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
