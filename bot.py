import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# =======================
# إعداد البوت
# =======================
import os 
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # تأكد من تعيين المتغير البيئي TELEGRAM_BOT_TOKEN
ADMIN_ID = 5620024477
CHANNEL_LINK = "https://t.me/gmailfarmermax"

# =======================
# قاعدة البيانات
# =======================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول لو مش موجودة
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    available INTEGER DEFAULT 0,
    reserved INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    description TEXT,
    price INTEGER,
    status TEXT DEFAULT 'pending',
    proof TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    method TEXT,
    data TEXT,
    amount INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    task_completed INTEGER DEFAULT 0
)''')

conn.commit()

# =======================
# الوظائف الأساسية
# =======================

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        return {"id": row[0], "username": row[1], "available": row[2], "reserved": row[3], "referrals": row[4]}
    else:
        return None

def add_task(user_id, description, price):
    cursor.execute("INSERT INTO tasks (user_id, description, price) VALUES (?, ?, ?)", (user_id, description, price))
    conn.commit()
    return cursor.lastrowid

def get_tasks(user_id):
    cursor.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
    return cursor.fetchall()

def add_withdrawal(user_id, method, data, amount):
    cursor.execute("INSERT INTO withdrawals (user_id, method, data, amount) VALUES (?, ?, ?, ?)", (user_id, method, data, amount))
    conn.commit()
    return cursor.lastrowid

# =======================
# أوامر المستخدم
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    add_user(user_id, username)
    msg = f"أهلاً 👋\nمرحبًا كل شيء بسيط وسهل، ستقوم بعمل مهمات مقابل مكافآت.\nيرجى الانضمام للقناة أولاً: {CHANNEL_LINK}"
    await update.message.reply_text(msg)
    await show_menu(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("طلب مهمة جديدة", callback_data="new_task")],
        [InlineKeyboardButton("رصيدي", callback_data="balance")],
        [InlineKeyboardButton("مهامي", callback_data="my_tasks")],
        [InlineKeyboardButton("سحب الأرباح", callback_data="withdraw")],
        [InlineKeyboardButton("الإحالات", callback_data="referrals")],
        [InlineKeyboardButton("مساعدة", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# =======================
# التعامل مع الأزرار
# =======================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)

    if query.data == "new_task":
        task_price = 10  # مثال على سعر المهمة، المشرف يقدر يغير
        task_id = add_task(user_id, "مهمة جديدة", task_price)
        await query.edit_message_text(f"✅ تم طلب مهمة جديدة.\nسعر المهمة: {task_price} وحدة\nفي انتظار بيانات المشرف.")

        # إشعار للمشرف
        await context.bot.send_message(ADMIN_ID, f"المستخدم {user_id} طلب مهمة جديدة.\nTask ID: {task_id}\nيرجى إرسال بيانات المهمة.")

    elif query.data == "balance":
        msg = (
            f"ID: {user['id']}\n"
            f"رصيد متاح: {user['available']}\n"
            f"رصيد محجوز: {user['reserved']}\n"
            f"رصيد الإحالات: {user['referrals']}\n\n"
            "(الرصيد المحجوز يتحول لرصيد متاح بعد 48 ساعة)"
        )
        await query.edit_message_text(msg)

    elif query.data == "my_tasks":
        tasks_list = get_tasks(user_id)
        if not tasks_list:
            await query.edit_message_text("ليس لديك مهام حالياً.")
            return
        msg = "مهامك:\n"
        for t in tasks_list:
            msg += f"Task ID {t[0]} - {t[3]} وحدة - الحالة: {t[4]}\n"
        await query.edit_message_text(msg)

    elif query.data == "help":
        msg = (
            "ℹ️ المساعدة\n\n"
            "📋 طلب مهمة: اطلب مهمة جديدة\n"
            "💰 رصيدي: عرض رصيدك الحالي\n"
            "📊 مهامي: عرض قائمة مهامك\n"
            "💸 سحب الأرباح: طلب سحب الأرباح\n"
            "👥 الإحالات: عرض رابط الإحالة الخاص بك\n"
            "🎬 طريقة عمل المهمة: شاهد فيديو توضيحي\n\n"
            "💡 كيف يعمل النظام:\n"
            "1. اطلب مهمة جديدة\n"
            "2. ستحصل على بيانات الحساب\n"
            "3. أنشئ الحساب وأرسل الإثبات\n"
            "4. بعد الموافقة تحصل على المكافأة\n\n"
            "📞 للدعم الفني: @gmailfarmermaxsupport"
        )
        await query.edit_message_text(msg)

    elif query.data == "withdraw":
        keyboard = [
            [InlineKeyboardButton("Vodafone Cash", callback_data="withdraw_vodafone")],
            [InlineKeyboardButton("InstaPay", callback_data="withdraw_insta")],
            [InlineKeyboardButton("Binance Pay", callback_data="withdraw_binance")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختر طريقة السحب:", reply_markup=reply_markup)

    elif query.data.startswith("withdraw_"):
        method = query.data.split("_")[1]
        await query.edit_message_text(f"✉️ أرسل بيانات السحب لطريقة {method} وسيتم إرسال الطلب للمشرف.")
        # هنا يقدر المستخدم يرسل بيانات السحب في رسالة لاحقة

    else:
        await query.edit_message_text("⚠️ هذه الميزة قيد التطوير...")

# =======================
# تشغيل البوت
# =======================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", show_menu))
app.add_handler(CallbackQueryHandler(button_handler))

print("🤖 البوت بدأ يشتغل...")
app.run_polling()
