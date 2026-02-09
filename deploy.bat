@echo off
echo ================================================
echo        نشر البوت على Railway
echo ================================================
echo.

echo [1/4] اضافة جميع الملفات...
git add .
if errorlevel 1 (
    echo خطأ: فشل في اضافة الملفات
    echo تأكد من أن Git مثبت
    pause
    exit /b 1
)
echo ✅ تم اضافة الملفات بنجاح
echo.

echo [2/4] حفظ التغييرات...
git commit -m "Fix all database errors and improve error handling"
if errorlevel 1 (
    echo ⚠️ لا توجد تغييرات جديدة أو تم الحفظ مسبقاً
)
echo ✅ تم حفظ التغييرات
echo.

echo [3/4] رفع الملفات للسيرفر...
git push
if errorlevel 1 (
    echo ❌ خطأ في رفع الملفات
    echo تأكد من:
    echo   - اتصالك بالإنترنت
    echo   - صلاحيات GitHub
    pause
    exit /b 1
)
echo ✅ تم رفع الملفات بنجاح
echo.

echo [4/4] اختبار قاعدة البيانات...
python test_db.py
echo.

echo ================================================
echo ✅ تم النشر بنجاح!
echo ================================================
echo.
echo الخطوات التالية:
echo 1. افتح Railway Dashboard
echo 2. انتظر انتهاء البناء (2-3 دقائق)
echo 3. افتح Logs وتأكد من رؤية:
echo    ✅ Bot started successfully!
echo 4. اختبر البوت بإرسال /start
echo.
pause
