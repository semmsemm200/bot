# إعداد قاعدة البيانات للبوت

## المشكلة
البيانات تُمسح بعد كل تحديث على Heroku/Render لأن هذه المنصات تستخدم نظام ملفات مؤقت.

## الحل: استخدام PostgreSQL

### على Heroku:

1. **إضافة PostgreSQL Add-on:**
```bash
heroku addons:create heroku-postgresql:mini
```

2. **التحقق من إضافة DATABASE_URL:**
```bash
heroku config
```
يجب أن ترى `DATABASE_URL` في القائمة.

3. **Deploy البوت:**
```bash
git push heroku main
```

### على Render:

1. **إنشاء PostgreSQL Database:**
   - اذهب إلى Dashboard
   - اضغط "New +" → "PostgreSQL"
   - اختر الخطة المجانية
   - انسخ "Internal Database URL"

2. **إضافة DATABASE_URL للبوت:**
   - اذهب لإعدادات البوت
   - اضغط "Environment"
   - أضف متغير جديد:
     - Key: `DATABASE_URL`
     - Value: [الصق الـ URL اللي نسخته]

3. **Redeploy البوت:**
   - اضغط "Manual Deploy" → "Deploy latest commit"

### ملاحظات مهمة:

- ✅ البيانات الآن محفوظة بشكل دائم
- ✅ لن تُمسح البيانات بعد التحديثات
- ✅ البوت يدعم SQLite للتطوير المحلي و PostgreSQL للإنتاج تلقائياً
- ⚠️ تأكد من عمل backup للبيانات بشكل دوري

### التحقق من نجاح الإعداد:

بعد Deploy، شغل البوت وأضف مستخدم جديد، ثم اعمل Redeploy. 
إذا بقيت البيانات موجودة، يبقى الإعداد نجح! ✅
