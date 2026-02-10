#!/usr/bin/env python3
"""
سكريبت لاختبار اتصال PostgreSQL
"""
import os
import sys

print("=" * 70)
print("🔍 اختبار اتصال PostgreSQL")
print("=" * 70)

# Check environment variables
print("\n1️⃣ فحص متغيرات البيئة:")
print("-" * 70)

database_url = os.environ.get('DATABASE_URL')
pghost = os.environ.get('PGHOST')
pguser = os.environ.get('PGUSER')
pgdatabase = os.environ.get('PGDATABASE')
pgpassword = os.environ.get('PGPASSWORD')
pgport = os.environ.get('PGPORT')

if database_url:
    print("✅ DATABASE_URL موجود")
    # Hide password
    if '@' in database_url:
        parts = database_url.split('@')
        safe_url = parts[0].split(':')[0] + ':***@' + parts[1]
        print(f"   📍 {safe_url}")
else:
    print("❌ DATABASE_URL غير موجود")

print(f"\n   PGHOST: {'✅ ' + pghost if pghost else '❌ غير موجود'}")
print(f"   PGUSER: {'✅ ' + pguser if pguser else '❌ غير موجود'}")
print(f"   PGDATABASE: {'✅ ' + pgdatabase if pgdatabase else '❌ غير موجود'}")
print(f"   PGPASSWORD: {'✅ موجود' if pgpassword else '❌ غير موجود'}")
print(f"   PGPORT: {'✅ ' + pgport if pgport else '❌ غير موجود (افتراضي: 5432)'}")

# Try to connect
print("\n2️⃣ محاولة الاتصال:")
print("-" * 70)

if not database_url and not (pghost and pgdatabase):
    print("❌ لا يوجد معلومات اتصال PostgreSQL!")
    print("\n🚨 المشكلة:")
    print("   PostgreSQL موجودة لكن غير متصلة بالبوت")
    print("\n✅ الحل:")
    print("   1. تأكد أن PostgreSQL في نفس المشروع مع البوت")
    print("   2. أو أضف DATABASE_URL يدوياً في Variables")
    sys.exit(1)

# Build connection URL
if not database_url:
    pguser = pguser or 'postgres'
    pgport = pgport or '5432'
    database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
    print("🔄 تم بناء DATABASE_URL من المتغيرات الفردية")

# Fix postgres:// to postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    print("🔄 تم تحويل postgres:// إلى postgresql://")

# Try to connect
try:
    import psycopg2
    print("\n✅ مكتبة psycopg2 مثبتة")
    
    print("🔄 محاولة الاتصال بـ PostgreSQL...")
    conn = psycopg2.connect(database_url, sslmode='require')
    cursor = conn.cursor()
    
    print("✅ الاتصال نجح!")
    
    # Test query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n📊 إصدار PostgreSQL:")
    print(f"   {version[:50]}...")
    
    # Check tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    print(f"\n📋 الجداول الموجودة ({len(tables)}):")
    if tables:
        for table in tables:
            print(f"   ✅ {table[0]}")
    else:
        print("   ⚠️ لا توجد جداول بعد (سيتم إنشاؤها عند تشغيل البوت)")
    
    # Check users count
    try:
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 عدد المستخدمين: {user_count}")
        
        if user_count > 0:
            print("✅ يوجد مستخدمين - البيانات محفوظة!")
        else:
            print("⚠️ لا يوجد مستخدمين بعد")
            print("   اضغط /start في البوت لإضافة أول مستخدم")
    except Exception as e:
        print(f"\n⚠️ جدول users غير موجود بعد: {e}")
        print("   سيتم إنشاؤه عند تشغيل البوت")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("🎉 الاتصال ناجح - PostgreSQL تعمل بشكل صحيح!")
    print("=" * 70)
    print("\n✅ البيانات ستُحفظ تلقائياً من البوت")
    print("✅ لا تحتاج إدخال بيانات يدوياً")
    
except ImportError:
    print("\n❌ مكتبة psycopg2 غير مثبتة!")
    print("\n✅ الحل:")
    print("   pip install psycopg2-binary")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ فشل الاتصال: {e}")
    print("\n🔍 الأسباب المحتملة:")
    print("   1. PostgreSQL غير شغالة")
    print("   2. معلومات الاتصال خاطئة")
    print("   3. مشكلة في الشبكة")
    print("\n✅ الحل:")
    print("   1. تحقق من أن PostgreSQL Active في Railway")
    print("   2. أعد تشغيل PostgreSQL")
    print("   3. أعد تشغيل البوت")
    sys.exit(1)

print("\n" + "=" * 70)
