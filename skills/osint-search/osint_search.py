import re, sys, html, urllib.parse, urllib.request

# القائمة البيضاء: وكالات + صحف عالمية وعربية + مراكز أبحاث (سياسية/عسكرية)
DOMAINS = [
    # وكالات عالمية
    "reuters.com", "apnews.com", "afp.com", "bloomberg.com", "bbc.com/news", "cnn.com", "nbcnews.com",
    "dw.com", "france24.com", "euronews.com",
    # وكالات إقليمية/رسمية
    "spa.gov.sa", "irna.ir", "isna.ir", "mehrnews.com", "wafa.ps", "maannews.net",
    # صحافة عربية/إقليمية موثوقة
    "alarabiya.net", "aawsat.com", "aljazeera.net", "aljazeera.com", "rt.com/arabic", "skynewsarabia.com",
    "okaz.com.sa", "sabq.org", "alriyadh.com", "alhayat.com", "alquds.co.uk", "alahram.org.eg",
    # صحافة إسرائيلية/أمريكية متخصصة
    "timesofisrael.com", "jpost.com", "foreignaffairs.com", "foreignpolicy.com",
    # مراكز أبحاث دولية
    "csis.org", "rand.org", "chathamhouse.org", "iiss.org", "carnegieendowment.org", "carnegie-mec.org",
    "brookings.edu", "ecfr.eu", "mei.edu", "washingtoninstitute.org", "inss.org.il", "icg.org",
    "rusi.org", "atlanticcouncil.org", "cfr.org", "pomeps.org", "timep.org", "palestine-studies.org",
    # مراكز أبحاث عربية/خليجية
    "dohainstitute.org", "studies.aljazeera.net", "kfcris.com", "fikercenter.com", "epc.ae",
    "kapsarc.org", "arabcenterdc.org", "grc.net", "memri.org", "amayaf.org",
]

def search_whitelist(query, max_results=10):
    """بحث في القائمة البيضاء عبر Google News RSS (المحرك الوحيد المثبت عمليًا من هذا الجهاز)."""
    params = {"q": query, "hl": "ar", "gl": "sa", "ceid": "SA:ar"}
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            xml = resp.read().decode("utf-8", "ignore")
    except Exception as e:
        return f"### OSINT — خطأ في الاتصال بمحرك الأخبار: {str(e)}"

    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    if not items:
        return f"### OSINT — لا نتائج لـ: {query}"

    filtered = []
    for it in items:
        src = re.search(r'<source[^>]*url="([^"]*)"[^>]*>(.*?)</source>', it, re.S)
        source_url = (src.group(1) or "").lower()
        if any(d in source_url for d in DOMAINS):
            t = re.search(r"<title>(.*?)</title>", it, re.S)
            l = re.search(r"<link>(.*?)</link>", it, re.S)
            d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
            filtered.append({
                "title": html.unescape(re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", t.group(1), flags=re.S)).strip() if t else "",
                "link": (l.group(1) if l else "").strip(),
                "source": html.unescape(src.group(2)).strip() if src else "؟",
                "date": d.group(1).strip() if d else "",
            })

    if not filtered:
        return (f"### OSINT — لا نتائج ضمن القائمة البيضاء لـ: {query}\n"
                f"💡 النتائج العامة وصلت لكنها من خارج النطاقات البيضاء المعتمدة.")

    out = [f"### OSINT — نتائج القائمة البيضاء لـ: {query}"]
    for r in filtered[:max_results]:
        out.append(f"- **{r['title']}**")
        out.append(f"  المصدر: {r['source']} | {r['date']}")
        out.append(f"  🔗 {r['link']}")
    return "\n".join(out)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("خطأ: يجب إدخال كلمة مفتاحية للبحث.")
        sys.exit(1)
    print(search_whitelist(" ".join(sys.argv[1:])))
