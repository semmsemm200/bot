# إعداد قاعدة البيانات للبوت

## 🔴 المشكلة
البيانات تُمسح بعد كل تحديث على Heroku/Render لأن هذه المنصات تستخدم نظام ملفات مؤقت.

## ✅ الحل السريع

البوت **جاهز** للعمل مع PostgreSQL! فقط أضف `DATABASE_URL` وخلاص.

---

## 📋 الخطوات حسب المنصة:

### 🟣 على Heroku:

#### من Terminal/CMD:
```bash
heroku login
heroku addons:create heroku-postgresql:essential-0
```

#### أو من Dashboard:
1. اذهب لتطبيقك على Heroku
2. اضغط **Resources**
3. ابحث عن **Heroku Postgres**
4. اختر **Essential 0** (مجاني - 10,000 صف)
5. اضغط **Submit Order Form**

#### التحقق:
```bash
heroku config
```
يجب أن ترى: `DATABASE_URL: postgres://...`

---

### 🟢 على Render:

#### 1. إنشاء قاعدة البيانات:
1. اذهب إلى [Render Dashboard](https://dashboard.render.com/)
2. اضغط **New +** → **PostgreSQL**
3. املأ البيانات:
   - **Name**: bot-database
   - **Database**: bot_db
   - **Region**: اختر أقرب منطقة
   - **Plan**: **Free** (1 GB)
4. اضغط **Create Database**

#### 2. انسخ Database URL:
- من صفحة القاعدة → **Connections**
- انسخ **Internal Database URL** (يبدأ بـ `postgresql://...`)

#### 3. أضف للبوت:
1. اذهب لصفحة البوت (Web Service)
2. **Environment** → **Add Environment Variable**
3. أضف:
   - **Key**: `DATABASE_URL`
   - **Value**: [الصق الـ URL]
4. **Save Changes**

البوت سيعمل Redeploy تلقائياً!

---

### 🔵 على Railway:

1. Dashboard → **New** → **Database** → **PostgreSQL**
2. انسخ **DATABASE_URL** من Variables
3. اذهب للبوت → **Variables**
4. أضف: `DATABASE_URL` = [الـ URL]

---

## ✅ بعد الإعداد:

### التحقق من نجاح الإعداد:
1. شغل البوت وأضف مستخدم جديد
2. اعمل Redeploy
3. تحقق أن المستخدم لسه موجود ✅

### المميزات:
- ✅ البيانات محفوظة بشكل دائم
- ✅ لن تُمسح البيانات بعد التحديثات
- ✅ البوت يدعم SQLite للتطوير المحلي و PostgreSQL للإنتاج تلقائياً
- ✅ Backup تلقائي (على Heroku)
- ⚠️ تأكد من عمل backup للبيانات بشكل دوري

---

## 🔧 معلومات تقنية:

### كيف يعمل البوت؟
```python
# البوت يتحقق تلقائياً من DATABASE_URL
if DATABASE_URL:
    # استخدم PostgreSQL
else:
    # استخدم SQLite (محلي فقط)
```

### الخطط المجانية:
- **Heroku**: Essential 0 - 10,000 صف
- **Render**: Free - 1 GB Storage
- **Railway**: 500 MB Storage

---

## ❓ الأسئلة الشائعة:

**س: هل أحتاج تعديل الكود؟**
ج: لا! البوت جاهز تماماً.

**س: ماذا عن البيانات القديمة؟**
ج: للأسف، البيانات المحلية ضاعت. ابدأ من جديد.

**س: هل PostgreSQL صعب؟**
ج: لا! فقط أضف DATABASE_URL وخلاص.

**س: كم تكلفة PostgreSQL؟**
ج: مجاني تماماً على الخطط المذكورة!

---

## 🆘 محتاج مساعدة؟

إذا واجهت مشكلة:
1. تأكد أن DATABASE_URL موجود في Environment Variables
2. تأكد أن الـ URL يبدأ بـ `postgresql://` (مش `postgres://`)
3. جرب Redeploy البوت
4. شوف logs للبوت لو في أخطاء
