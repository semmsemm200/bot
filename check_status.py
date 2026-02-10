#!/usr/bin/env python3
"""
سكريبت للتحقق من حالة البوت وقاعدة البيانات
"""
import os

print("=" * 60)
print("🔍 فحص حالة البوت")
print("=" * 60)

# Check environment variables
print("\n📊 متغيرات البيئة:")
print("-" * 60)

telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
database_url = os.environ.get('DATABASE_URL')
pghost = os.environ.get('PGHOST')
pgdatabase = os.environ.get('PGDATABASE')

if telegram_token:
    print("✅ TELEGRAM_BOT_TOKEN موجود")
else:
    print("❌ TELEGRAM_BOT_TOKEN غير موجود!")

if database_url:
    print("✅ DATABASE_URL موجود (PostgreSQL)")
    # Hide password
    if '@' in database_url:
        parts = database_url.split('@')
        safe_url = parts[0].split(':')[0] + ':***@' + parts[1]
        print(f"   📍 {safe_url}")
elif pghost and pgdatabase:
    print("✅ PGHOST و PGDATABASE موجودين (PostgreSQL)")
    print(f"   📍 Host: {pghost}")
    print(f"   📍 Database: {pgdatabase}")
else:
    print("❌ لا يوجد PostgreSQL!")
    print("⚠️  البوت سيستخدم SQLite (البيانات ستُمسح عند redeploy)")

print("\n" + "=" * 60)
print("📋 التشخيص:")
print("=" * 60)

if database_url or (pghost and pgdatabase):
    print("\n✅ PostgreSQL متصل!")
    print("✅ البيانات ستُحفظ تلقائياً من البوت")
    print("✅ لا تحتاج إدخال بيانات يدوياً")
    print("\n🎯 الخطوات التالية:")
    print("   1. شغّل البوت")
    print("   2. اضغط /start في Telegram")
    print("   3. البوت سيضيفك تلقائياً في database")
    print("   4. اعمل redeploy - البيانات ستبقى!")
else:
    print("\n❌ PostgreSQL غير متصل!")
    print("⚠️  البيانات ستُمسح عند كل redeploy")
    print("\n🚨 الحل:")
    print("   1. افتح Railway Dashboard")
    print("   2. اضغط + New → Database → Add PostgreSQL")
    print("   3. انتظر 30 ثانية")
    print("   4. أعد تشغيل البوت")
    print("\n📖 اقرأ: اقرأني_مهم.md")

print("\n" + "=" * 60)

# Try to check database
print("\n🔌 محاولة الاتصال بقاعدة البيانات:")
print("-" * 60)

try:
    import db
    print("\n✅ تم استيراد db.py بنجاح")
    print(f"📊 نوع قاعدة البيانات: {db.DB_TYPE}")
    
    if db.DB_TYPE == 'postgresql':
        print("✅ متصل بـ PostgreSQL")
        print("✅ البيانات محفوظة!")
        
        # Try to get user count
        try:
            count = db.get_user_count()
            print(f"\n👥 عدد المستخدمين الحالي: {count}")
            
            if count == 0:
                print("\n💡 لا يوجد مستخدمين بعد")
                print("   اضغط /start في البوت لإضافة أول مستخدم")
            else:
                print("\n✅ يوجد مستخدمين في database")
                print("   البيانات محفوظة بشكل صحيح!")
        except Exception as e:
            print(f"\n⚠️ خطأ في قراءة البيانات: {e}")
            print("   قد تحتاج إلى تشغيل البوت أولاً لإنشاء الجداول")
    else:
        print("❌ متصل بـ SQLite (محلي)")
        print("⚠️  البيانات ستُمسح عند redeploy!")
        print("\n🚨 أضف PostgreSQL الآن!")
        
except Exception as e:
    print(f"\n❌ خطأ: {e}")
    print("\n💡 تأكد من:")
    print("   1. تثبيت المكتبات: pip install -r requirements.txt")
    print("   2. وجود ملف db.py")

print("\n" + "=" * 60)
print("✅ انتهى الفحص")
print("=" * 60)
