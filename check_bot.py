#!/usr/bin/env python3
"""
فحص سريع للبوت - اكتشاف المشاكل
"""

import sys
import os

print("=" * 60)
print("🔍 فحص البوت - اكتشاف المشاكل")
print("=" * 60)
print()

# Test 1: Check Python version
print("1️⃣ فحص إصدار Python...")
print(f"   Python: {sys.version}")
if sys.version_info < (3, 8):
    print("   ❌ Python قديم! يجب 3.8 أو أحدث")
else:
    print("   ✅ إصدار Python مناسب")
print()

# Test 2: Check required modules
print("2️⃣ فحص المكتبات المطلوبة...")
required_modules = {
    'telegram': 'python-telegram-bot',
    'psycopg2': 'psycopg2-binary',
}

missing = []
for module, package in required_modules.items():
    try:
        __import__(module)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} - غير مثبت!")
        missing.append(package)

if missing:
    print()
    print("   ⚠️ لتثبيت المكتبات الناقصة:")
    print(f"   pip install {' '.join(missing)}")
print()

# Test 3: Check config
print("3️⃣ فحص ملف الإعدادات...")
try:
    import config
    
    if hasattr(config, 'TOKEN') and config.TOKEN:
        print(f"   ✅ BOT_TOKEN موجود (يبدأ بـ {config.TOKEN[:10]}...)")
    else:
        print("   ❌ BOT_TOKEN غير موجود!")
    
    if hasattr(config, 'ADMIN_ID') and config.ADMIN_ID:
        print(f"   ✅ ADMIN_ID موجود: {config.ADMIN_ID}")
    else:
        print("   ❌ ADMIN_ID غير موجود!")
        
except Exception as e:
    print(f"   ❌ خطأ في قراءة config.py: {e}")
print()

# Test 4: Check database connection
print("4️⃣ فحص الاتصال بقاعدة البيانات...")
try:
    import db
    
    # Check database type
    print(f"   📊 نوع قاعدة البيانات: {db.DB_TYPE}")
    
    if db.DB_TYPE == 'postgresql':
        if os.environ.get('DATABASE_URL'):
            print(f"   ✅ DATABASE_URL موجود")
        else:
            print(f"   ❌ DATABASE_URL غير موجود!")
    
    # Try to initialize
    print("   🔄 محاولة تهيئة قاعدة البيانات...")
    db.init_db()
    print("   ✅ تم تهيئة قاعدة البيانات بنجاح")
    
    # Try a simple query
    print("   🔄 محاولة قراءة الإعدادات...")
    task_price = db.get_setting("task_price")
    if task_price:
        print(f"   ✅ قراءة البيانات تعمل (سعر المهمة: {task_price})")
    else:
        print("   ⚠️ لم يتم العثور على إعدادات (قاعدة بيانات جديدة؟)")
        
except Exception as e:
    print(f"   ❌ خطأ في قاعدة البيانات: {e}")
    import traceback
    print()
    print("   📋 تفاصيل الخطأ:")
    traceback.print_exc()
print()

# Test 5: Check handlers
print("5️⃣ فحص ملفات المعالجات...")
files_to_check = [
    'bot.py',
    'db.py',
    'config.py',
    'handlers_admin.py',
    'handlers_user.py',
    'helpers.py'
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - غير موجود!")
print()

# Test 6: Try to import bot
print("6️⃣ فحص استيراد ملف البوت...")
try:
    import bot
    print("   ✅ تم استيراد bot.py بنجاح")
except Exception as e:
    print(f"   ❌ خطأ في استيراد bot.py: {e}")
    import traceback
    print()
    print("   📋 تفاصيل الخطأ:")
    traceback.print_exc()
print()

# Summary
print("=" * 60)
print("📊 ملخص الفحص")
print("=" * 60)

issues = []

# Check if we can proceed
try:
    import config
    if not hasattr(config, 'TOKEN') or not config.TOKEN:
        issues.append("❌ BOT_TOKEN غير موجود في config.py")
    if not hasattr(config, 'ADMIN_ID') or not config.ADMIN_ID:
        issues.append("❌ ADMIN_ID غير موجود في config.py")
except:
    issues.append("❌ لا يمكن قراءة config.py")

if missing:
    issues.append(f"❌ مكتبات ناقصة: {', '.join(missing)}")

if issues:
    print()
    print("⚠️ المشاكل المكتشفة:")
    for issue in issues:
        print(f"   {issue}")
    print()
    print("🔧 يجب حل هذه المشاكل قبل تشغيل البوت")
else:
    print()
    print("✅ كل شيء يبدو جيداً!")
    print()
    print("🚀 يمكنك تشغيل البوت الآن:")
    print("   python bot.py")

print()
print("=" * 60)
