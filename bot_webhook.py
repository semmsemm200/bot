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
import os
from aiohttp import web


# Import message handlers from bot.py
from bot import handle_message, handle_photo, handle_video, callback_router


# ==================== WEBHOOK SETUP ====================
async def webhook_update(request):
    """Handle incoming webhook updates"""
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return web.Response(status=500)


async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="Bot is running!")


# ==================== MAIN ====================
def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!")
        return

    print("=" * 50)
    print("Starting Bot with Webhook...")
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
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connection_pool_size=8,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0
        )
        
        global app
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
        
        # Get webhook URL from environment
        PORT = int(os.environ.get('PORT', 8080))
        RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        RAILWAY_STATIC_URL = os.environ.get('RAILWAY_STATIC_URL')
        
        # Determine webhook URL
        if RAILWAY_PUBLIC_DOMAIN:
            WEBHOOK_URL = f"https://{RAILWAY_PUBLIC_DOMAIN}/webhook"
        elif RAILWAY_STATIC_URL:
            WEBHOOK_URL = f"{RAILWAY_STATIC_URL}/webhook"
        else:
            print("⚠️ No Railway domain found, using polling mode")
            print("=" * 50)
            print("✅ Bot started successfully!")
            print("=" * 50)
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            return
        
        print(f"Setting webhook to: {WEBHOOK_URL}")
        
        # Setup webhook
        import asyncio
        async def setup_webhook():
            await app.bot.set_webhook(
                url=WEBHOOK_URL,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            print(f"✅ Webhook set successfully!")
        
        asyncio.run(setup_webhook())
        
        # Setup web server
        web_app = web.Application()
        web_app.router.add_post('/webhook', webhook_update)
        web_app.router.add_get('/health', health_check)
        web_app.router.add_get('/', health_check)
        
        print("=" * 50)
        print("✅ Bot started successfully with Webhook!")
        print(f"📡 Webhook URL: {WEBHOOK_URL}")
        print(f"🌐 Port: {PORT}")
        print("=" * 50)
        
        # Start web server
        web.run_app(web_app, host='0.0.0.0', port=PORT)
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
