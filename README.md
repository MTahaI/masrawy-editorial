# نسخة احتياطية لنظام التحرير — دليل إعادة البناء من الصفر

> هذه النسخة تحفظ **كل عمل غير قابل للتعويض** (إعدادات + قواعد + سكيلز + مشروع تحريري).
> النماذج المحلية (1.17GB) **لا تُحفظ هنا** — تُعاد تحميلها عبر `ollama pull` (انظر الخطوة 4).
> المفاتيح **لا تُحفظ هنا أبدًا** — توضع في متغيرات البيئة (الخطوة 5).

## محتويات النسخة
| المجلد | المحتوى |
|---|---|
| `config/` | `opencode.jsonc` — ملف إعدادات أوبن كود الكامل (الموفرون، سيرفرات MCP، التعليمات) |
| `rules/` | القواعد التحريرية السبع (الدستور، النبرة، البروتوكولات، التحقق المصادري، أتمتة التحقق...) |
| `skills/` | المهارات: buriedsignals (19 سكيلز تحقيق) + مهارات النظام العربية |
| `project/` | مشروع التحرير `D:\مصراوي` (دليل الأسلوب، AGENTS.md...) |
| `tools/` | تعديلات الأدوات المثبتة يدويًا |

## استراتيجية البحث والاستخراج (بلا أي مفتاح مدفوع)
- **البحث عن المصادر:** أداة websearch المدمجة في أوبن كود (مجانية، مثبتة الجودة في الاختبار الشامل).
- **رادار الأخبار العربية:** سكربت `tools/news-radar/news_search.py` — بحث فوري في Google News RSS بلا مفاتيح
  (`python news_search.py --query "..." --region sa --lang ar --max 10`). يعمل من جهازنا (مثبت: 92 نتيجة عربية).
- **البحث الحديث المقيّد زمنيًا:** `--hours 2` يقصر النتائج على آخر ساعتين حسب تاريخ النشر الفعلي (مثبت: دقة إلى الدقيقة،
  ويعرض عمر كل خبر "منذ X دقيقة"). يُستخدم إلزاميًا عند طلب "بحث حديث/آخر أخبار".
- **بحث مراكز الأبحاث:** سكربت `tools/think-tank-search/think_tank_search.py` — RSS مباشر + site:، يعرض اسم المحلل والجهة،
  ومع `--extract` يفتح أفضل 5 نتائج ويبني روابط تمييز نصي `#:~:text=` (استخدم الكلمة بلغتين: `"اليمن Yemen"`).
- **استخراج المحتوى:** سيرفر MCP `fetch` الرسمي (`python -m mcp_server_fetch` من PyPI) + webfetch المدمج.
- **الصفحات العنيدة/الجافافاسكريبت:** puppeteer-server ثم مسار الطوارئ Jina Reader:
  `https://r.jina.ai/<URL>` (مجاني بلا مفتاح للاستخدام المحدود).
- **لا Tavily ولا Exa** — أُزيلا نهائيًا (كانا معطوبين بمفاتيح مدفوعة غير صالحة).
- **ملاحظة بحث 2026-08:** DuckDuckGo وMojeek محجوبان/ضعيفان من هذا الجهاز؛ Google News RSS هو المحرك المجاني الموثوق عمليًا.
  مهارة `osint-search` أُصلحت لتعتمد عليه مع فلترة إلزامية على القائمة البيضاء (وكالات + صحافة عربية + مراكز أبحاث).

## إعادة البناء على جهاز جديد (بالترتيب)

### 1. الأدوات الأساسية
- تثبيت: Node.js ≥ 20، Python ≥ 3.11، Git، OpenCode Desktop
- تثبيت Ollama: https://ollama.com/download

### 2. الإعدادات
- انسخ `config/opencode.jsonc` إلى `C:\Users\<اسمك>\.config\opencode\opencode.jsonc`
- انسخ `rules/` إلى `C:\Users\<اسمك>\.config\opencode\rules\`
- انسخ `skills/` إلى `C:\Users\<اسمك>\.config\opencode\skills\`
- انسخ `project/` إلى `D:\مصراوي\` (أو أي مسار تريده)

### 3. الحزمة اليدوية المطلوبة لأوبن كود
```powershell
cd "$env:USERPROFILE\.config\opencode"
npm init -y
npm install @ai-sdk/openai-compatible
```
(هذه الحزمة ضرورية لتشغيل مزود Ollama المحلي داخل أوبن كود)

### 4. النماذج المحلية (Ollama)
```powershell
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text:latest
# إعادة بناء النموذج المعدل (سياق 8192):
ollama create qwen2.5:1.5b-ctx -f tools/Modelfile-ctx
```

### 5. المفاتيح (متغيرات البيئة — مستوى User)
```
GEMINI_API_KEY   ← من Google AI Studio (لـ news-factcheck و Gemini)
GROQ_API_KEY     ← من console.groq.com (للمحرر السحابي)
```
> لا حاجة لأي مفتاح آخر: البحث والاستخراج والتحقق كلها مجانية (websearch + fetch + corroborate + footnote).
تثبيت عبر: إعدادات Windows → النظام → حول → إعدادات النظام المتقدمة → متغيرات البيئة.

### 6. أدوات MCP (تثبيت لمرة واحدة)
```powershell
# footnote (التحقق بالاستلزام)
pip install footnote-mcp
python -m playwright install chromium   # اختياري لكن موصى به

# news-factcheck (فحص العناوين بـ Gemini) — يُثبت في C:\Users\<اسمك>\Tools\
git clone https://github.com/adityapawar327/news-factchecker-mcp.git C:\Users\<اسمك>\Tools\news-factchecker
pip install -r C:\Users\<اسمك>\Tools\news-factchecker\requirements.txt

# local-rag (فهرسة محلية) — يُثبت في C:\Users\<اسمك>\Tools\
git clone https://github.com/overlorde/local-rag-mcp.git C:\Users\<اسمك>\Tools\local-rag-mcp
# استبدل config.py بالنسخة المعدلة في tools/local-rag-config.py (نماذج صغيرة)
pip install -r C:\Users\<اسمك>\Tools\local-rag-mcp\requirements.txt
```
ملاحظات:
- `corroborate` (npx -y corroborate-mcp) يُحمَّل تلقائيًا من npm — لا يحتاج تثبيتًا.
- `puppeteer-server` و`gdelt` منصات Remote/موجودة في الإعدادات. (`tavily` أُزيل نهائيًا من الإعدادات.)
- إعدادات MCP موجودة أصلًا في `config/opencode.jsonc` — لا حاجة لإعادة كتابتها.

### 7. إعادة التشغيل والتحقق
- أعد تشغيل OpenCode Desktop كليًا
- تحقق: `/models` يعرض qwen2.5:1.5b و qwen2.5:1.5b-ctx و gemini-3.5-flash
- تحقق: سيرفرات MCP السبعة تظهر (puppeteer, fetch, gdelt, corroborate, footnote, local-rag, news-factcheck)

## حماية النسخة
- هذا المستودع **خاص** — لا تجعله عامًا أبدًا.
- **لا ترفع المفاتيح** إلى هذا المستودع تحت أي ظرف (متغيرات البيئة فقط).
- شغّل `backup.ps1` بعد كل جلسة عمل لتحديث النسخة ودفعها للمستودع.

## ملاحظة أمان عاجلة
- إذا انكشف أي مفتاح في محادثة أو ملف محلي: **ألغِه فورًا** من لوحة تحكم المزود وولّد بديلًا.
- النسخ الاحتياطية القديمة لأوبن كود (`workspace\backup`) قد تحتوي مفاتيح مضمّنة — احذفها ولا ترفعها.
