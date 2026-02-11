import os
import db
from config import TOKEN, ADMIN_ID
from helpers import is_admin, get_main_menu_keyboard, send_to_admins, send_photo_to_admins
from handlers_user import (
    start, check_subscription, verify_subscription, menu_command, back_to_menu,
    new_task, admin_send_task_data, task_done, task_cancel, task_how_to,
    admin_approve_task, admin_reject_task, admin_error_task,
    balance, my_tasks, withdraw, withdraw_method_selected,
    withdrawal_history, referrals, my_referrals_list, leaderboard, withdraw_referral,
    help_cmd, tutorial,
    new_task_text, balance_text, my_tasks_text, withdraw_text,
    referrals_text, withdraw_referral_text, tutorial_text, help_text,
    admin_panel_text
)
from handlers_admin import (
    admin_panel, admin_pending_tasks, admin_withdrawals,
    admin_approve_withdrawal, admin_reject_withdrawal,
    admin_users, admin_users_list, admin_reserved, admin_reserved_user_tasks, 
    admin_release_all_user_tasks, admin_release_task, admin_task_details,
    admin_settings, admin_toggle_bot,
    admin_set_task_price, admin_set_price_value, admin_set_ref_reward, admin_set_ref_value,
    admin_set_min_w, admin_set_minw_value,
    admin_set_fees, admin_edit_method, admin_method_min, admin_set_method_min_value,
    admin_method_fee, admin_set_method_fee_value,
    admin_add_method, admin_search_user, admin_view_user, admin_clear_balance, admin_do_clear_balance,
    admin_cancel_task_prompt, admin_do_cancel_task, admin_manage_admins,
    admin_add_admin, admin_remove_admin, admin_set_video,
    admin_reward_user, admin_reward_select_user, admin_reward_amount,
    admin_ban_user, admin_do_ban_user, admin_toggle_bot_with_notification
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)


# ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin: sending task data
    if context.user_data.get("admin_sending_data_for_task") and is_admin(user_id):
        task_id = context.user_data.pop("admin_sending_data_for_task")
        task = db.get_task(task_id)
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة.")
            return
        db.update_task_admin_data(task_id, text)
        keyboard = [
            [InlineKeyboardButton("تم التنفيذ", callback_data=f"task_done_{task_id}")],
            [InlineKeyboardButton("إلغاء المهمة", callback_data=f"task_cancel_{task_id}")],
            [InlineKeyboardButton("كيفية عمل المهمة", callback_data=f"task_howto_{task_id}")],
        ]
        try:
            await context.bot.send_message(
                task["user_id"],
                f"بيانات المهمة #{task_id}:\n\n{text}\n\nسعر المهمة: {task['price']} جنيه",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text(
                f"✅ تم إرسال البيانات بنجاح\n"
                f"🆔 المهمة: #{task_id}\n"
                f"👤 المستخدم: {task['user_id']}"
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ تعذر إرسال البيانات للمستخدم: {str(e)}")
        return

    # Admin: error description for task
    if context.user_data.get("admin_error_task_id") and is_admin(user_id):
        task_id = context.user_data.pop("admin_error_task_id")
        task = db.get_task(task_id)
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة.")
            return
        db.set_task_error(task_id, text)
        try:
            await context.bot.send_message(
                task["user_id"],
                f"⚠️ خطأ في المهمة #{task_id}:\n{text}\n\nيرجى إصلاح الخطأ وإرسال إثبات جديد (صورة)."
            )
            # Store that this user needs to resubmit
            if "resubmit_tasks" not in context.bot_data:
                context.bot_data["resubmit_tasks"] = {}
            context.bot_data["resubmit_tasks"][str(task["user_id"])] = task_id
            await update.message.reply_text(
                f"✅ تم إرسال الخطأ بنجاح\n"
                f"🆔 المهمة: #{task_id}\n"
                f"👤 المستخدم: {task['user_id']}"
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ تم حفظ الخطأ لكن تعذر إرسال الإشعار: {str(e)}")
        return

    # Admin: custom task price input
    if context.user_data.get("admin_setting_task_price") and is_admin(user_id):
        context.user_data.pop("admin_setting_task_price")
        try:
            price = int(text)
            if price <= 0:
                await update.message.reply_text("❌ يجب أن يكون السعر أكبر من صفر.")
                return
            db.set_setting("task_price", str(price))
            await update.message.reply_text(f"✅ تم تغيير سعر المهمة إلى {price} جنيه")
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح فقط.")
        return

    # Admin: custom referral reward input
    if context.user_data.get("admin_setting_ref_reward") and is_admin(user_id):
        context.user_data.pop("admin_setting_ref_reward")
        try:
            reward = int(text)
            if reward < 0:
                await update.message.reply_text("❌ يجب أن تكون المكافأة صفر أو أكبر.")
                return
            db.set_setting("referral_reward", str(reward))
            await update.message.reply_text(f"✅ تم تغيير مكافأة الإحالة إلى {reward} جنيه")
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح فقط.")
        return

    # Admin: custom min withdrawal input
    if context.user_data.get("admin_setting_min_withdrawal") and is_admin(user_id):
        context.user_data.pop("admin_setting_min_withdrawal")
        try:
            min_w = int(text)
            if min_w <= 0:
                await update.message.reply_text("❌ يجب أن يكون الحد الأدنى أكبر من صفر.")
                return
            db.set_setting("min_withdrawal", str(min_w))
            await update.message.reply_text(f"✅ تم تغيير الحد الأدنى للسحب إلى {min_w} جنيه")
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال رقم صحيح فقط.")
        return

    # Admin: adding new admin
    if context.user_data.get("admin_adding_admin") and is_admin(user_id):
        context.user_data.pop("admin_adding_admin")
        try:
            new_admin_id = int(text)
            if is_admin(new_admin_id):
                await update.message.reply_text("⚠️ هذا المستخدم مشرف بالفعل.")
                return
            db.add_admin(new_admin_id)
            await update.message.reply_text(f"✅ تم إضافة المشرف {new_admin_id} بنجاح.")
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال ID صحيح (رقم فقط).")
        return

    # Admin: removing admin
    if context.user_data.get("admin_removing_admin") and is_admin(user_id):
        context.user_data.pop("admin_removing_admin")
        try:
            admin_id_to_remove = int(text)
            if admin_id_to_remove == ADMIN_ID:
                await update.message.reply_text("❌ لا يمكن إزالة المشرف الرئيسي.")
                return
            if not is_admin(admin_id_to_remove):
                await update.message.reply_text("⚠️ هذا المستخدم ليس مشرفاً.")
                return
            db.remove_admin(admin_id_to_remove)
            await update.message.reply_text(f"✅ تم إزالة المشرف {admin_id_to_remove} بنجاح.")
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال ID صحيح (رقم فقط).")
        return

    # User: withdrawal data
    if context.user_data.get("withdraw_method"):
        method_name = context.user_data.pop("withdraw_method")
        user = db.get_user(user_id)
        if not user:
            return
        amount = user["available"]
        method = db.get_withdrawal_method(method_name)
        fee = method["fee"] if method else 0
        final_amount = amount - fee
        if final_amount <= 0:
            await update.message.reply_text("⚠️ رصيدك لا يكفي بعد خصم الرسوم.")
            return
        db.update_user_balance(user_id, available=0)
        wid = db.create_withdrawal(user_id, method_name, text, amount)
        await update.message.reply_text(
            f"✅ تم إرسال طلب السحب #{wid} بنجاح\n"
            f"📱 الطريقة: {method_name}\n"
            f"💰 المبلغ: {amount} جنيه\n"
            f"💸 الرسوم: {fee} جنيه\n"
            f"⏳ في انتظار موافقة المشرف."
        )
        kb = [
            [InlineKeyboardButton("✅ قبول", callback_data=f"admin_approve_w_{wid}"),
             InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_w_{wid}")]
        ]
        await send_to_admins(context,
            f"💸 طلب سحب جديد #{wid}\n"
            f"👤 مستخدم: {user_id}\n"
            f"📱 الطريقة: {method_name}\n"
            f"📝 البيانات: {text}\n"
            f"💰 المبلغ: {amount} جنيه",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # Handle keyboard button presses
    if text == "📋 طلب مهمة جديدة":
        await new_task_text(update, context)
    elif text == "💰 رصيدي":
        await balance_text(update, context)
    elif text == "📊 مهامي":
        await my_tasks_text(update, context)
    elif text == "💸 سحب الأرباح":
        await withdraw_text(update, context)
    elif text == "👥 الإحالات":
        await referrals_text(update, context)
    elif text == "💎 سحب رصيد الإحالات":
        await withdraw_referral_text(update, context)
    elif text == "🎬 طريقة عمل المهمة":
        await tutorial_text(update, context)
    elif text == "ℹ️ مساعدة":
        await help_text(update, context)
    elif text == "🔧 لوحة الإدارة" and is_admin(user_id):
        await admin_panel_text(update, context)
    else:
        # Default
        await update.message.reply_text("اختر من القائمة:", reply_markup=get_main_menu_keyboard(user_id))


# ==================== PHOTO HANDLER ====================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id

    # User: submitting task proof
    if context.user_data.get("submitting_proof_for_task"):
        task_id = context.user_data.pop("submitting_proof_for_task")
        task = db.get_task(task_id)
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة.")
            return
        db.update_task_proof(task_id, file_id)
        await update.message.reply_text(f"✅ تم إرسال الإثبات للمهمة #{task_id} بنجاح. في انتظار مراجعة المشرف.")
        kb = [
            [InlineKeyboardButton("موافقة", callback_data=f"admin_approve_t_{task_id}")],
            [InlineKeyboardButton("رفض", callback_data=f"admin_reject_t_{task_id}")],
            [InlineKeyboardButton("خطأ في التنفيذ", callback_data=f"admin_error_t_{task_id}")],
        ]
        await send_photo_to_admins(context, file_id,
            f"📸 إثبات المهمة #{task_id}\n👤 مستخدم: {task['user_id']}\n💰 السعر: {task['price']} جنيه",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # User: resubmitting proof after error
    resubmit_tasks = context.bot_data.get("resubmit_tasks", {})
    user_key = str(user_id)
    if user_key in resubmit_tasks:
        task_id = resubmit_tasks.pop(user_key)
        task = db.get_task(task_id)
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة.")
            return
        db.update_task_error_resubmit(task_id, file_id)
        await update.message.reply_text(f"✅ تم إرسال الإثبات الجديد للمهمة #{task_id} بنجاح. في انتظار مراجعة المشرف.")
        kb = [
            [InlineKeyboardButton("موافقة", callback_data=f"admin_approve_t_{task_id}")],
            [InlineKeyboardButton("رفض", callback_data=f"admin_reject_t_{task_id}")],
            [InlineKeyboardButton("خطأ في التنفيذ", callback_data=f"admin_error_t_{task_id}")],
        ]
        await send_photo_to_admins(context, file_id,
            f"📸 إثبات معاد للمهمة #{task_id}\n👤 مستخدم: {task['user_id']}\n💰 السعر: {task['price']} جنيه",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # Admin: sending withdrawal receipt
    if context.user_data.get("admin_approve_withdrawal_id") and is_admin(user_id):
        wid = context.user_data.pop("admin_approve_withdrawal_id")
        w = db.get_withdrawal(wid)
        if not w:
            await update.message.reply_text("❌ طلب السحب غير موجود.")
            return
        db.approve_withdrawal(wid)
        db.set_withdrawal_receipt(wid, file_id)
        try:
            await context.bot.send_photo(
                w["user_id"], file_id,
                caption=f"✅ تم تنفيذ طلب السحب #{wid}\n💰 المبلغ: {w['amount']} جنيه\n📱 الطريقة: {w['method']}"
            )
            await update.message.reply_text(
                f"✅ تم قبول طلب السحب بنجاح\n"
                f"🆔 الطلب: #{wid}\n"
                f"👤 المستخدم: {w['user_id']}\n"
                f"💰 المبلغ: {w['amount']} جنيه"
            )
        except Exception as e:
            await update.message.reply_text(f"✅ تم قبول الطلب لكن تعذر إرسال الإيصال: {str(e)}")
        return

    await update.message.reply_text("اختر من القائمة:", reply_markup=get_main_menu_keyboard(user_id))


# ==================== VIDEO HANDLER ====================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get("admin_setting_video") and is_admin(user_id):
        context.user_data.pop("admin_setting_video")
        video = update.message.video
        if video:
            db.set_setting("tutorial_video_id", video.file_id)
            await update.message.reply_text("✅ تم حفظ فيديو الشرح بنجاح.")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال فيديو.")
        return
    await update.message.reply_text("اختر من القائمة:", reply_markup=get_main_menu_keyboard(user_id))


# ==================== CALLBACK ROUTER ====================
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "verify_subscription":
        await verify_subscription(update, context)
    elif data == "check_sub":
        await check_subscription(update, context)
    elif data == "back_menu":
        await back_to_menu(update, context)
    elif data == "new_task":
        await new_task(update, context)
    elif data == "balance":
        await balance(update, context)
    elif data == "my_tasks":
        await my_tasks(update, context)
    elif data == "withdraw":
        await withdraw(update, context)
    elif data == "referrals":
        await referrals(update, context)
    elif data == "my_referrals_list":
        await my_referrals_list(update, context)
    elif data == "leaderboard":
        await leaderboard(update, context)
    elif data == "withdraw_referral":
        await withdraw_referral(update, context)
    elif data == "help":
        await help_cmd(update, context)
    elif data == "tutorial":
        await tutorial(update, context)
    elif data == "withdrawal_history":
        await withdrawal_history(update, context)
    elif data.startswith("task_done_"):
        await task_done(update, context)
    elif data.startswith("task_cancel_"):
        await task_cancel(update, context)
    elif data.startswith("task_howto_"):
        await task_how_to(update, context)
    elif data.startswith("admin_send_data_"):
        await admin_send_task_data(update, context)
    elif data.startswith("admin_approve_t_"):
        await admin_approve_task(update, context)
    elif data.startswith("admin_reject_t_"):
        await admin_reject_task(update, context)
    elif data.startswith("admin_error_t_"):
        await admin_error_task(update, context)
    elif data.startswith("wmethod_"):
        await withdraw_method_selected(update, context)
    elif data == "admin_panel":
        await admin_panel(update, context)
    elif data == "admin_pending_tasks":
        await admin_pending_tasks(update, context)
    elif data == "admin_withdrawals":
        await admin_withdrawals(update, context)
    elif data.startswith("admin_approve_w_"):
        await admin_approve_withdrawal(update, context)
    elif data.startswith("admin_reject_w_"):
        await admin_reject_withdrawal(update, context)
    elif data == "admin_users":
        await admin_users(update, context)
    elif data == "admin_users_list":
        await admin_users_list(update, context)
    elif data == "admin_reserved":
        await admin_reserved(update, context)
    elif data.startswith("admin_reserved_user_"):
        await admin_reserved_user_tasks(update, context)
    elif data.startswith("admin_release_all_"):
        await admin_release_all_user_tasks(update, context)
    elif data.startswith("admin_release_"):
        await admin_release_task(update, context)
    elif data.startswith("admin_task_details_"):
        await admin_task_details(update, context)
    elif data == "admin_settings":
        await admin_settings(update, context)
    elif data == "admin_toggle_bot":
        await admin_toggle_bot_with_notification(update, context)
    elif data == "admin_set_task_price":
        await admin_set_task_price(update, context)
    elif data.startswith("admin_price_"):
        await admin_set_price_value(update, context)
    elif data == "admin_set_ref_reward":
        await admin_set_ref_reward(update, context)
    elif data.startswith("admin_ref_"):
        await admin_set_ref_value(update, context)
    elif data == "admin_set_min_w":
        await admin_set_min_w(update, context)
    elif data.startswith("admin_minw_"):
        await admin_set_minw_value(update, context)
    elif data == "admin_set_fees":
        await admin_set_fees(update, context)
    elif data.startswith("admin_method_min_"):
        await admin_method_min(update, context)
    elif data.startswith("admin_setmin_"):
        await admin_set_method_min_value(update, context)
    elif data.startswith("admin_method_fee_"):
        await admin_method_fee(update, context)
    elif data.startswith("admin_setfee_"):
        await admin_set_method_fee_value(update, context)
    elif data.startswith("admin_edit_method_"):
        await admin_edit_method(update, context)
    elif data == "admin_add_method":
        await admin_add_method(update, context)
    elif data == "admin_search_user":
        await admin_search_user(update, context)
    elif data.startswith("admin_view_user_"):
        await admin_view_user(update, context)
    elif data == "admin_clear_balance":
        await admin_clear_balance(update, context)
    elif data.startswith("admin_do_clear_"):
        await admin_do_clear_balance(update, context)
    elif data == "admin_cancel_task":
        await admin_cancel_task_prompt(update, context)
    elif data.startswith("admin_do_cancel_"):
        await admin_do_cancel_task(update, context)
    elif data == "admin_reward_user":
        await admin_reward_user(update, context)
    elif data.startswith("admin_reward_select_"):
        await admin_reward_select_user(update, context)
    elif data.startswith("admin_reward_amount_"):
        await admin_reward_amount(update, context)
    elif data == "admin_ban_user":
        await admin_ban_user(update, context)
    elif data.startswith("admin_do_ban_"):
        await admin_do_ban_user(update, context)
    elif data == "admin_manage_admins":
        await admin_manage_admins(update, context)
    elif data == "admin_add_admin":
        await admin_add_admin(update, context)
    elif data == "admin_remove_admin":
        await admin_remove_admin(update, context)
    elif data == "admin_set_video":
        await admin_set_video(update, context)
    else:
        await query.answer("غير معروف", show_alert=True)


# ==================== MAIN ====================
def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Set it with: export TELEGRAM_BOT_TOKEN=your_token_here")
        return

    print("=" * 50)
    print("Starting Bot...")
    print("=" * 50)
    
    try:
        print("Initializing database...")
        db.init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return
    
    try:
        print("Building application...")
        # Increase timeouts for Railway
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connection_pool_size=8,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0
        )
        
        app = (
            ApplicationBuilder()
            .token(TOKEN)
            .request(request)
            .build()
        )
        
        print("Adding handlers...")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("menu", menu_command))
        app.add_handler(CallbackQueryHandler(callback_router))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.VIDEO, handle_video))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("=" * 50)
        print("✅ Bot started successfully!")
        print("=" * 50)
        print("البوت بدأ يشتغل...")
        
        # Use Polling with drop_pending_updates to avoid conflicts
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
