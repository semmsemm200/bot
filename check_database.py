#!/usr/bin/env python3
"""
سكريبت للتحقق من حالة قاعدة البيانات
"""
import os
import sys

print("=" * 50)
print("🔍 فحص إعدادات قاعدة البيانات")
print("=" * 50)

# Check DATABASE_URL
database_url = os.environ.get('DATABASE_URL')

if database_url:
    print("\n✅ DATABASE_URL موجود!")
    print(f"📊 النوع: PostgreSQL")
    
    # Hide sensitive info
    if '@' in database_url:
        parts = database_url.split('@')
        safe_url = parts[0].split(':')[0] + ':***@' + parts[1]
        print(f"🔗 URL: {safe_url}")
    
    # Try to connect
    try:
        import psycopg2
        print("\n🔌 محاولة الاتصال...")
        
        # Fix Heroku URL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        conn = psycopg2.connect(database_url, sslmode='require')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print("✅ الاتصال نجح!")
        print(f"\n📋 الجداول الموجودة ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check users count
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 عدد المستخدمين: {user_count}")
        except:
            print("\n⚠️ جدول المستخدمين غير موجود بعد")
        
        conn.close()
        print("\n🎉 قاعدة البيانات تعمل بشكل صحيح!")
        
    except ImportError:
        print("\n⚠️ مكتبة psycopg2 غير مثبتة")
        print("قم بتثبيتها: pip install psycopg2-binary")
    except Exception as e:
        print(f"\n❌ خطأ في الاتصال: {e}")
        print("\n💡 تأكد من:")
        print("  1. DATABASE_URL صحيح")
        print("  2. قاعدة البيانات تعمل")
        print("  3. الاتصال بالإنترنت متاح")

else:
    print("\n❌ DATABASE_URL غير موجود!")
    print("\n📊 النوع: SQLite (محلي)")
    print("⚠️ البيانات ستُمسح عند إعادة النشر!")
    
    # Check SQLite file
    if os.path.exists('bot.db'):
        import sqlite3
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 عدد المستخدمين (محلي): {user_count}")
        except:
            print("\n⚠️ قاعدة البيانات فارغة")
        
        conn.close()
    else:
        print("\n⚠️ ملف bot.db غير موجود")
    
    print("\n" + "=" * 50)
    print("🔴 يجب إضافة PostgreSQL على المنصة!")
    print("=" * 50)
    print("\n📖 اقرأ ملف FIX_NOW.md للحل")

print("\n" + "=" * 50)
