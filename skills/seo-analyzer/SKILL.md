---
name: seo-analyzer
description: يفحص النص لضمان توافقه مع SEO. المعامل الأول: الكلمة المفتاحية (keyword). المعامل الثاني: نص المقال (content).
---

# seo-analyzer

نفّذ: `python C:/Users/m122s/.config/opencode/skills/seo_analyzer.py "{{keyword}}" "{{content}}"`

المعامل الأول `keyword` هو الكلمة المفتاحية، والمعامل الثاني `content` هو نص المقال (يُمرَّر بين علامتي تنصيص).

النتيجة النصية تُعاد كما وردت دون تحوير، ويُنفَّذ التقرير (ضبط الكثافة + إضافة الكلمة للعناوين الناقصة + Meta Description ≤ 160 حرفًا) تحت مسؤولية مدير التحرير.
