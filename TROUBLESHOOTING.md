# دليل حل المشاكل - Troubleshooting Guide

## المشكلة: البوت وقف خالص

### الخطوات التشخيصية:

## 1️⃣ تحقق من الأخطاء في Railway

افتح Railway Dashboard → اضغط على البوت → اذهب لـ **Deployments** → اضغط على آخر deployment → اضغط على **View Logs**

ابحث عن:
- ❌ أخطاء Python (Traceback)
- ❌ أخطاء قاعدة البيانات
- ❌ أخطاء الاتصال

---

## 2️⃣ اختبار قاعدة البيانات محلياً

قبل النشر، اختبر قاعدة البيانات:

```bash
python test_db.py
```

يجب أن ترى:
```
✅ Database initialized successfully
✅ Task price: 10
✅ User added successfully
✅ Total users: X
```

إذا رأيت أخطاء، أرسلها لي.

---

## 3️⃣ تحقق من متغيرات البيئة في Railway

في Railway Dashboard:
1. اذهب لـ **Variables**
2. تأكد من وجود:
   - ✅ `BOT_TOKEN` - توكن البوت من BotFather
   - ✅ `ADMIN_ID` - ID الخاص بك
   - ✅ `DATABASE_URL` - يتم إضافته تلقائياً من PostgreSQL

---

## 4️⃣ الأخطاء الشائعة وحلولها

### خطأ: `current transaction is aborted`
**الحل:** تم إصلاحه في آخر تحديث! تأكد من رفع الكود الجديد.

```bash
git add .
git commit -m "Fix all database transaction errors"
git push
```

### خطأ: `Bot token is invalid`
**الحل:** 
1. احصل على توكن جديد من @BotFather
2. في Railway → Variables → عدل `BOT_TOKEN`
3. أعد تشغيل البوت

### خطأ: `Connection refused` أو `Timeout`
**الحل:**
1. تأكد من أن PostgreSQL database مفعل في Railway
2. تأكد من أن `DATABASE_URL` موجود في Variables
3. أعد تشغيل البوت

### خطأ: `Module not found`
**الحل:** تأكد من أن `requirements.txt` يحتوي على:
```
python-telegram-bot==20.7
psycopg2-binary
```

---

## 5️⃣ إعادة تشغيل البوت في Railway

### الطريقة 1: من Dashboard
1. اذهب لـ Railway Dashboard
2. اضغط على البوت
3. اضغط على **Settings**
4. اضغط على **Restart**

### الطريقة 2: Push جديد
```bash
git add .
git commit -m "Restart bot" --allow-empty
git push
```

---

## 6️⃣ التحقق من حالة البوت

أرسل `/start` للبوت في Telegram:
- ✅ إذا رد → البوت يعمل
- ❌ إذا لم يرد → البوت متوقف

---

## 7️⃣ فحص Logs في الوقت الفعلي

في Railway:
1. اذهب لـ **Deployments**
2. اضغط على آخر deployment
3. اضغط على **View Logs**
4. شاهد الأخطاء في الوقت الفعلي

ابحث عن:
```
Starting Bot...
Bot started successfully!
```

إذا رأيت هذه الرسائل، البوت يعمل.

---

## 8️⃣ إعادة إنشاء قاعدة البيانات (الحل الأخير)

⚠️ **تحذير: هذا سيمسح جميع البيانات!**

إذا كانت قاعدة البيانات تالفة:

1. في Railway Dashboard → اذهب لـ PostgreSQL
2. اضغط على **Settings**
3. اضغط على **Delete Service**
4. أضف PostgreSQL جديد:
   - اضغط **+ New**
   - اختر **Database**
   - اختر **Add PostgreSQL**
5. انتظر حتى يتم إنشاء `DATABASE_URL`
6. أعد تشغيل البوت

---

## 9️⃣ الحصول على المساعدة

إذا جربت كل الحلول ولم يعمل البوت:

1. **افتح Railway Logs**
2. **انسخ آخر 20-30 سطر من الأخطاء**
3. **أرسلها لي** مع وصف المشكلة

مثال:
```
البوت وقف بعد ما ضغطت على "الرصيد المحجوز"
الخطأ في Logs:
[error message here]
```

---

## 🔟 نصائح للوقاية

### ✅ افعل:
- اختبر التغييرات محلياً قبل النشر
- راقب Logs بعد كل تحديث
- احتفظ بنسخة احتياطية من قاعدة البيانات

### ❌ لا تفعل:
- لا تشغل نسختين من البوت بنفس التوكن
- لا تعدل قاعدة البيانات يدوياً
- لا تحذف متغيرات البيئة

---

## الملفات المهمة للمراجعة

إذا كان البوت لا يعمل، راجع:

1. **db.py** - قاعدة البيانات
2. **bot.py** - الملف الرئيسي
3. **handlers_admin.py** - وظائف الإدارة
4. **handlers_user.py** - وظائف المستخدمين
5. **requirements.txt** - المكتبات المطلوبة

---

## اختبار سريع

قبل النشر، شغل:
```bash
python test_db.py
```

إذا نجح الاختبار، البوت جاهز للنشر! 🚀
