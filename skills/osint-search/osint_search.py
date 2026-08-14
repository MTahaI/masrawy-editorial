import sys
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("خطأ: يرجى تثبيت المكتبة عبر الأمر: pip install ddgs")
        sys.exit(1)

# القائمة البيضاء المعزولة
DOMAINS = [
    "reuters.com", "apnews.com", "afp.com", "bloomberg.com", "bbc.com/news", "cnn.com", "nbcnews.com", "dw.com", "france24.com", "euronews.com",
    "irna.ir", "isna.ir", "mehrnews.com", "iranintl.com",
    "wafa.ps", "maannews.net", "ajnet.me",
    "timesofisrael.com", "jpost.com", "foreignaffairs.com", "foreignpolicy.com",
    "csis.org", "rand.org", "chathamhouse.org", "iiss.org", "carnegieendowment.org", "brookings.edu", "ecfr.eu", "mei.edu", "washingtoninstitute.org", "inss.org.il", "pomeps.org", "timep.org", "icg.org", "rusi.org", "atlanticcouncil.org", "cfr.org", "palestine-studies.org", "studies.aljazeera.net"
]

def search_whitelist(query):
    results_out = f"### 🔍 استخبارات المصادر المفتوحة (OSINT) - نتائج البحث لـ: {query}\n"
    
    try:
        with DDGS() as ddgs:
            # سحب 100 نتيجة لضمان شبكة بحث أوسع، بدون قيود زمنية تعيق النتائج
            raw_results = list(ddgs.text(query, max_results=100))
    except Exception as e:
        return results_out + f"\n⚠️ حدث خطأ أثناء الاتصال بمحرك البحث: {str(e)}"
        
    if not raw_results:
        return results_out + "\n⚠️ محرك البحث لم يُرجع أي نتائج. قد يكون هناك حظر مؤقت من DuckDuckGo."

    filtered_results = []
    # فلترة النتائج لمطابقة القائمة البيضاء فقط
    for res in raw_results:
        link = res.get("href", "").lower()
        if any(domain in link for domain in DOMAINS):
            filtered_results.append(res)
            
    if not filtered_results:
        results_out += f"\n⚠️ تم سحب {len(raw_results)} نتيجة من الإنترنت، لكن تم رفضها جميعاً لأنها من مواقع خارج القائمة البيضاء المعتمدة.\n"
        results_out += "💡 نصيحة استخباراتية: ابحث عن (الحدث) مباشرة وليس (اسم الوكالة). السكربت سيفلتر الوكالات تلقائياً."
        return results_out
        
    for r in filtered_results[:10]: # عرض أعلى 10 نتائج مطابقة
        results_out += f"- **{r.get('title', 'بدون عنوان')}**\n"
        results_out += f"  🔗 الرابط: {r.get('href', '#')}\n"
        results_out += f"  📄 الملخص: {r.get('body', 'لا يوجد ملخص')}\n\n"
        
    return results_out

if __name__ == "__main__":
    # ضمان طباعة UTF-8 على Windows (الإيموجي 🔍 والرموز العربية خارج cp1252)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        print("خطأ: يجب إدخال كلمة مفتاحية للبحث.")
        sys.exit(1)
    
    # دمج كل الكلمات الممررة ككلمة مفتاحية واحدة
    query = " ".join(sys.argv[1:])
    print(search_whitelist(query))