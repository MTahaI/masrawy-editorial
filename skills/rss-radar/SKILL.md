---
name: rss-radar
description: رادار الأخبار اللحظي. يجب تمرير اسم المنصة كمعامل (masrawy أو weaam) لكي يقوم السكربت بجلب الأخبار المناسبة للهوية.
---

# rss-radar

نفّذ: `python C:/Users/m122s/.config/opencode/skills/rss_radar.py "{{platform}}"`

المعامل `platform` كلمة واحدة فقط:
- `masrawy` — البنك المحلي المصري (القاهرة 24، اليوم السابع، فيتو، المصري اليوم، القاهرة الإخبارية) + رويترز بالعربية (عبر Google News لأن خلاصة feeds.reuters.com الرسمية معطلة منذ مارس 2026) + مصادر إنجليزية موثوقة (BBC، Guardian، CNN، NYT، DW، France24، Axios) + مراكز فكر (Atlantic Council، ECFR، Stimson) + مصادر إيرانية (Mehr مباشرة، Fars عبر Google News؛ تسنيم غير متاح — DNS معطل + Google News صفر) + رادار Currents اللحظي.
- `weaam` — البنك المحلي السعودي (الشرق الأوسط بخلاصة رسمية مباشرة، واس/سبق/الرياض عبر Google News لأن خلاصاتهم المباشرة صفر/404، الصفحات السعودية على إكس عبر Google News لأن RSSHub العام معطل 404) + رويترز بالعربية + أكسيوس + رادار Currents اللحظي.

مصادر مُختبَرة ورفضت لتعطلها الفعلي: AlJazeera EN (مهلة SSL متكررة)، Brookings/Carnegie (صفر أخبار)، Chatham House (403)، CFR/RAND/CSIS/Wilson/RUSI/Washington Institute (404)، Mehr بالعربية (404)، تسنيم (DNS).

النتيجة النصية تُعاد كما وردت دون تحوير، ويُوقف العمل عند السؤال النهائي بانتظار قرار رئيس التحرير قبل تنفيذ أي زاوية.
