# 🤖 بوت Gmail Farmer - Telegram Bot

## 📊 الحالة الحالية

### ✅ تم إصلاح جميع المشاكل:
- ✅ Timeout errors (30 ثانية)
- ✅ Transaction errors (rollback تلقائي)
- ✅ الرصيد المحجوز (يعمل بشكل صحيح)
- ✅ الاشتراك الإجباري (الأدمن يتجاوزه)
- ✅ إشعارات الإحالة (تعمل)
- ✅ جميع الأزرار (متناسقة)

### ⚠️ المطلوب منك:
**أضف PostgreSQL في Railway لحفظ البيانات!**

---

## 🚀 البدء السريع

### 1. أضف PostgreSQL
```
Railway Dashboard → + New → Database → Add PostgreSQL
```

### 2. أعد تشغيل البوت
```
Railway Dashboard → البوت → Settings → Restart
```

### 3. تحقق من النجاح
في Logs يجب أن ترى:
```
✅ Connected to PostgreSQL - Data will persist!
```

---

## 📁 الملفات المهمة

| الملف | الوصف |
|-------|-------|
| **اقرأني_مهم.md** | شرح سريع بالعربية (ابدأ من هنا!) |
| **DEPLOY_INSTRUCTIONS.md** | تعليمات النشر الكاملة |
| **FINAL_STATUS.md** | الحالة التفصيلية |
| **الوضع_الحالي.md** | ملخص الوضع الحالي |

---

## 🎯 الميزات

### للمستخدمين:
- 📋 طلب مهام جديدة
- 💰 عرض الرصيد (متاح، محجوز، إحالات)
- 📊 متابعة المهام
- 💸 سحب الأرباح (Vodafone Cash, InstaPay, Binance Pay)
- 👥 نظام الإحالات مع مكافآت
- 🏆 لوحة المتصدرين
- 🎬 فيديو شرح المهام

### للإدارة:
- 📋 إدارة المهام (قبول، رفض، خطأ)
- 💸 إدارة السحوبات
- 👥 إدارة المستخدمين
- 💎 إدارة الرصيد المحجوز
- ⚙️ الإعدادات (الأسعار، الرسوم، الحد الأدنى)
- 👨‍💼 إدارة المشرفين
- 🎁 مكافأة المستخدمين
- 🚫 حظر المستخدمين

---

## 🔧 المتطلبات

- Python 3.8+
- PostgreSQL (في Railway)
- Telegram Bot Token

---

## 📦 التثبيت المحلي (للتطوير)

```bash
# تثبيت المكتبات
pip install -r requirements.txt

# إعداد متغيرات البيئة
export TELEGRAM_BOT_TOKEN="your_token_here"

# تشغيل البوت
python bot.py
```

---

## 🌐 النشر على Railway

### الطريقة 1: Git
```bash
git add .
git commit -m "Deploy bot"
git push
```

### الطريقة 2: Railway CLI
```bash
railway up
```

---

## 📊 قاعدة البيانات

### الجداول:
- `users` - المستخدمين
- `tasks` - المهام
- `withdrawals` - السحوبات
- `referrals` - الإحالات
- `settings` - الإعدادات
- `admins` - المشرفين
- `withdrawal_methods` - طرق السحب

### الكشف التلقائي:
البوت يكتشف PostgreSQL تلقائياً عبر:
- `DATABASE_URL` (Railway)
- `PGHOST`, `PGPORT`, `PGDATABASE` (متغيرات فردية)

إذا لم يجد PostgreSQL، يستخدم SQLite (محلي فقط).

---

## 🆘 حل المشاكل

### البيانات تُمسح بعد Deploy
**الحل:** أضف PostgreSQL في Railway

### البوت لا يرد
**الحل:** تحقق من Logs وتأكد من صحة التوكن

### Timeout errors
**الحل:** تم إصلاحها في الكود (30 ثانية)

### Transaction errors
**الحل:** تم إصلاحها في الكود (rollback تلقائي)

---

## 📞 الدعم

اقرأ الملفات التالية للمساعدة:
- `اقرأني_مهم.md` - شرح سريع
- `DEPLOY_INSTRUCTIONS.md` - تعليمات مفصلة
- `TROUBLESHOOTING.md` - حل المشاكل

---

## 📝 الترخيص

هذا المشروع للاستخدام الشخصي.

---

**ابدأ الآن: أضف PostgreSQL في Railway!** 🚀
