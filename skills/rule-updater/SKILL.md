---
name: rule-updater
description: تضيف قاعدة تحريرية جديدة مباشرة إلى ملفات النظام. المعامل الأول: كلمة واحدة من (constitution, tone, protocols). المعامل الثاني: نص القاعدة.
---

# rule-updater

نفّذ: `python C:/Users/m122s/.config/opencode/skills/rule_updater.py "{{file_key}}" "{{new_rule}}"`

المعامل الأول `file_key` كلمة واحدة من: constitution, tone, protocols. المعامل الثاني `new_rule` هو نص القاعدة بين علامتي تنصيص.

النتيجة النصية (نجاح/خطأ) تُعاد كما وردت، وتُعرض على المستخدم للاعتماد.
