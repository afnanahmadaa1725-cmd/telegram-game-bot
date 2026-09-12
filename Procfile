رفع البوت إلى Render

ارفع الملفات الثلاثة إلى GitHub:
1. telegram_game_bot_render.py
2. render_requirements.txt
3. render.yaml

ثم في Render:
- New Web Service
- اختر مستودع GitHub
- Build Command:
  pip install -r render_requirements.txt
- Start Command:
  python telegram_game_bot_render.py
- أضف Environment Variable:
  BOT_TOKEN = توكن البوت

ملاحظة:
الخطة المجانية في Render لا تضمن تشغيل Web Service لمدة 24 ساعة بدون توقف؛ قد تدخل الخدمة في sleep أو يعاد تشغيلها وفق حدود وسياسة الخطة المجانية. لا يوجد تعديل برمجي يضمن 24/7 على خطة مجانية إذا كانت المنصة نفسها توقف الخدمة.

تمت إضافة Web Server صغير فقط ليتوافق الملف مع Web Service، ولم يتم تغيير منطق الألعاب.
