@echo off
echo ============================================================
echo        فحص سريع لحالة البوت
echo ============================================================
echo.

echo [1] التحقق من Python...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✅ Python موجود
    python --version
) else (
    echo    ❌ Python غير موجود
    echo    قم بتثبيت Python من: https://www.python.org/downloads/
)

echo.
echo [2] التحقق من المكتبات المطلوبة...
python -c "import telegram" >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✅ python-telegram-bot مثبتة
) else (
    echo    ❌ python-telegram-bot غير مثبتة
    echo    قم بتثبيتها: pip install python-telegram-bot
)

python -c "import psycopg2" >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✅ psycopg2 مثبتة
) else (
    echo    ⚠️  psycopg2 غير مثبتة (مطلوبة لـ PostgreSQL)
    echo    قم بتثبيتها: pip install psycopg2-binary
)

echo.
echo [3] التحقق من ملفات البوت...
if exist bot.py (
    echo    ✅ bot.py موجود
) else (
    echo    ❌ bot.py غير موجود!
)

if exist db.py (
    echo    ✅ db.py موجود
) else (
    echo    ❌ db.py غير موجود!
)

if exist config.py (
    echo    ✅ config.py موجود
) else (
    echo    ❌ config.py غير موجود!
)

echo.
echo [4] التحقق من متغيرات البيئة...
if defined TELEGRAM_BOT_TOKEN (
    echo    ✅ TELEGRAM_BOT_TOKEN موجود
) else (
    echo    ❌ TELEGRAM_BOT_TOKEN غير موجود
    echo    قم بتعيينه: set TELEGRAM_BOT_TOKEN=your_token_here
)

if defined DATABASE_URL (
    echo    ✅ DATABASE_URL موجود (PostgreSQL)
) else (
    echo    ⚠️  DATABASE_URL غير موجود (سيستخدم SQLite)
)

echo.
echo [5] التحقق من العمليات الجارية...
tasklist | findstr /i "python.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo    ⚠️  يوجد عمليات Python شغالة:
    tasklist | findstr /i "python.exe"
    echo.
    echo    إذا كان البوت شغال محلياً، أوقفه بـ Ctrl+C
) else (
    echo    ✅ لا توجد عمليات Python شغالة
)

echo.
echo ============================================================
echo                    التشخيص
echo ============================================================
echo.

if defined TELEGRAM_BOT_TOKEN (
    if exist bot.py (
        echo ✅ البوت جاهز للتشغيل محلياً
        echo.
        echo لتشغيل البوت محلياً:
        echo    python bot.py
        echo.
        echo ⚠️  تذكير: لا تشغل البوت محلياً إذا كان شغال على Railway!
    ) else (
        echo ❌ ملفات البوت ناقصة
    )
) else (
    echo ❌ TELEGRAM_BOT_TOKEN غير موجود
    echo.
    echo لتعيين Token:
    echo    set TELEGRAM_BOT_TOKEN=your_token_here
)

echo.
echo ============================================================
echo              للتحقق من البوت على Railway:
echo ============================================================
echo.
echo 1. افتح: https://railway.app
echo 2. اذهب للمشروع
echo 3. اضغط على البوت
echo 4. اضغط Deployments
echo 5. اضغط View Logs
echo.
echo ابحث عن:
echo    ✅ Connected to PostgreSQL - Data will persist!
echo    ✅ Bot started successfully!
echo.
echo ============================================================
echo.
pause
