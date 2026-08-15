#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
think_tank_search.py — البحث في مراكز الأبحاث (Think Tanks) السياسية والعسكرية
==============================================================================
يبحث في أحدث تحليلات مراكز الأبحاث المدرجة، ويعرضها باسم صاحب التحليل (إن وُجد)
والجهة الناشرة، مع استيراد النص الكامل للمقالات المطابقة وبناء روابط تمييز نصية
(Copy link to highlight: #:~:text=...).

الاستخدام:
  python think_tank_search.py --query "السعودية إيران" [--max 10] [--hours 48] [--strict] [--extract]

  --query     كلمات الموضوع (كلها يجب أن تظهر في المقال عند --strict، وإلا أيٌّ منها)
  --max       أقصى عدد نتائج (افتراضي 10)
  --hours     نافذة زمنية حسب تاريخ النشر (0 = بلا نافذة)
  --strict    المقال يجب أن يضم كل كلمات الاستعلام
  --extract   فتح أفضل النتائج، استخراج النص الكامل، وبناء روابط التمييز النصي

الملاحظة الصادقة: "اسم صاحب التحليل" يُستخرج من وسوم RSS (dc:creator أو نمط By X)؛
إذا لم تنشر الجهة اسم المحلل، يُذكر ذلك صراحةً.
"""
import argparse, datetime, html, json, re, sys, time, urllib.parse, urllib.request

# قائمة مراكز الأبحاث: RSS مباشرة فقط للمثبتة عمليًا + site: للبقية
THINK_TANKS = [
    {"name": "Atlantic Council",     "rss": "https://www.atlanticcouncil.org/feed/",      "site": "atlanticcouncil.org",     "type": "سياسي/عسكري دولي"},
    {"name": "ECFR",                 "rss": "https://ecfr.eu/feed/",                      "site": "ecfr.eu",                  "type": "سياسي أوروبي"},
    {"name": "Brookings",            "site": "brookings.edu",                            "type": "سياسي/اقتصادي دولي"},
    {"name": "Fiker Center",         "site": "fikercenter.com",                          "type": "فكري عربي"},
    {"name": "EPC (الإمارات للسياسات)", "site": "epc.ae",                                "type": "سياسات خليجية"},
    {"name": "KFCRIS (الملك فيصل)",  "site": "kfcris.com",                               "type": "دراسات إسلامية"},
    {"name": "Carnegie Endowment",   "site": "carnegieendowment.org",                    "type": "سياسي دولي"},
    {"name": "Carnegie MEC",         "site": "carnegie-mec.org",                         "type": "الشرق الأوسط"},
    {"name": "Chatham House",        "site": "chathamhouse.org",                         "type": "سياسة دولية"},
    {"name": "RAND",                 "site": "rand.org",                                 "type": "أمني/عسكري/سياسات"},
    {"name": "CSIS",                 "site": "csis.org",                                 "type": "استراتيجي/عسكري"},
    {"name": "Arab Center DC",       "site": "arabcenterdc.org",                         "type": "سياسات عربية"},
    {"name": "IISS",                 "site": "iiss.org",                                 "type": "عسكري/استراتيجي"},
    {"name": "CFR",                  "site": "cfr.org",                                  "type": "سياسة خارجية أمريكية"},
    {"name": "AlJazeera Studies",    "site": "studies.aljazeera.net",                    "type": "دراسات عربية"},
    {"name": "Doha Institute",       "site": "dohainstitute.org",                        "type": "دراسات عربية"},
    {"name": "KAPSARC",              "site": "kapsarc.org",                              "type": "طاقة/اقتصاد"},
]

def parse_pubdate(s: str):
    if not s:
        return None
    try:
        body = s.strip()
        if body.endswith("GMT"):
            body = body[:-3].strip()
        return datetime.datetime.strptime(body, "%a, %d %b %Y %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None

def clean(s):
    """إزالة وسوم CDATA وتنظيف النص."""
    if not s:
        return ""
    return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.S).strip()

def extract_author(title, desc, raw):
    """استخراج اسم المحلل: dc:creator ← By X ← نمط في الوصف/العنوان."""
    m = re.search(r"<dc:creator[^>]*>(.*?)</dc:creator>", raw, re.S | re.I)
    if m and m.group(1).strip():
        return clean(html.unescape(m.group(1).strip()))
    m = re.search(r"<author[^>]*>(.*?)</author>", raw, re.S | re.I)
    if m and m.group(1).strip():
        return clean(html.unescape(m.group(1).strip()))
    for text in (desc, title):
        m = re.search(r"\bBy\s+([A-Z][\w\u0600-\u06FF.\-' ]{2,60}?)(?:[|,<]|$)", text, re.I)
        if m:
            return m.group(1).strip().rstrip()
    m = re.search(r"بقلم[:\s]+([^,|]{3,60})", desc or "")
    if m:
        return m.group(1).strip()
    return None

def fetch_rss(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def rss_items(xml):
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    if not items:
        items = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    out = []
    for it in items:
        t = re.search(r"<title[^>]*>(.*?)</title>", it, re.S)
        l = re.search(r"<link[^>]*>(.*?)</link>", it, re.S)
        if not l:  # Atom
            l = re.search(r'<link[^>]*href="([^"]+)"', it)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S) or re.search(r"<updated>(.*?)</updated>", it, re.S)
        des = re.search(r"<description[^>]*>(.*?)</description>", it, re.S) or re.search(r"<summary[^>]*>(.*?)</summary>", it, re.S)
        out.append({
            "title": clean(html.unescape(re.sub(r"<[^>]+>", "", t.group(1)))) if t else "",
            "link": html.unescape(clean(l.group(1))) if l else "",
            "date": clean(d.group(1)) if d else "",
            "desc": clean(html.unescape(re.sub(r"<[^>]+>", "", des.group(1))))[:300] if des else "",
            "raw": it,
        })
    return out

def gnews_site(query, site, lang="en", region="US", max_items=5):
    """بحث Google News RSS مقيد بنطاق المركز (إضافة تلقائية عندما لا يعمل RSS مباشرة)."""
    q = f'"{query}" site:{site}'
    params = {"q": q, "hl": lang, "gl": region, "ceid": f"{region}:{lang}"}
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    try:
        xml = fetch_rss(url, timeout=15)
    except Exception:
        return []
    out = []
    for it in rss_items(xml)[:max_items]:
        src = re.search(r'<source[^>]*url="([^"]*)"[^>]*>(.*?)</source>', it["raw"], re.S)
        out.append({
            "title": it["title"], "link": it["link"], "date": it["date"], "desc": it["desc"],
            "source_name": html.unescape(src.group(2).strip()) if src else site,
            "author": None, "raw": it["raw"],
        })
    return out

def matches(text, keywords, strict):
    kws = [k for k in keywords if k]
    if not kws:
        return True
    low = text.lower()
    hits = sum(1 for k in kws if k.lower() in low)
    return hits == len(kws) if strict else hits > 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--hours", type=float, default=0)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--extract", action="store_true", help="استخراج كامل + روابط تمييز نصي")
    args = ap.parse_args()

    keywords = re.split(r"\s*[،,]\s*|\s+", args.query.strip())
    # ملاحظة: للبحث في المراكز الدولية استخدم الكلمة بلغتين: "اليمن Yemen" — أيُّهما يكفي دون --strict.
    cutoff = None
    if args.hours:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=args.hours)

    results = []
    for tt in THINK_TANKS:
        combined = []
        if tt.get("rss"):
            try:
                combined += rss_items(fetch_rss(tt["rss"]))
                for it in combined:
                    it["source_name"] = tt["name"]; it["author"] = extract_author(it["title"], it["desc"], it["raw"])
            except Exception:
                combined = []
        # إضافة تلقائية عبر site: دائمًا (لا نكتفي بـ RSS — يوسع التغطية)
        combined += gnews_site(args.query, tt["site"])
        for it in combined:
            dt = parse_pubdate(it["date"])
            # عنصر بلا تاريخ يبقى (قد يكون حديثًا) — لا يُحذف عند وجود نافذة
            if cutoff and dt is not None and dt < cutoff:
                continue
            hay = it["title"] + " " + it["desc"]
            if not matches(hay, keywords, args.strict):
                continue
            it["center"] = tt["name"]; it["center_type"] = tt["type"]
            results.append(it)

    results.sort(key=lambda x: parse_pubdate(x["date"]) or datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc), reverse=True)
    results = results[:args.max]

    if not results:
        print(json.dumps({"error": "no results from whitelisted think tanks", "query": args.query, "hours": args.hours}, ensure_ascii=False))
        return

    print(f"### مراكز الأبحاث — نتائج البحث لـ: {args.query} ({len(results)} نتيجة)")
    for i, it in enumerate(results, 1):
        author = it.get("author") or "بلا مؤلف صريح في المصدر"
        age = ""
        dt = parse_pubdate(it["date"])
        if dt:
            mins = int((datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 60)
            age = f" (منذ {mins} دقيقة)" if mins < 120 else f" ({it['date']})"
        print(f"\n[{i}] {it['title']}")
        print(f"    المحلل: {author}")
        print(f"    الجهة: {it.get('center')} — {it.get('center_type')} | المصدر: {it.get('source_name')}{age}")
        print(f"    الرابط: {it['link']}")
        if it.get("desc"):
            print(f"    مقتطف: {it['desc'][:160]}...")

    if args.extract:
        print("\n### الاستخراج الكامل + روابط التمييز النصي")
        NAV_NOISE = re.compile(r"subscribe|skip to content|rss feeds|newsletter|linkedin|bluesky|twitter|instagram|youtube|podcast|sign up|privacy policy|terms of use|all rights reserved|cookie", re.I)
        for i, it in enumerate(results[:5], 1):
            try:
                full = fetch_rss(it["link"], timeout=20)
            except Exception as e:
                print(f"\n[{i}] تعذر فتح المصدر: {str(e)[:80]}")
                continue
            # استخراج الفقرات الفعلية من وسوم <p> (يعزل نص المقال عن القوائم/الفوتر)
            raw_paras = re.findall(r"<p[^>]*>(.*?)</p>", full, re.S)
            paras = []
            for p in raw_paras:
                t = html.unescape(re.sub(r"<[^>]+>", " ", p))
                t = re.sub(r"\s+", " ", t).strip()
                if len(t) > 80 and not NAV_NOISE.search(t):
                    paras.append(t)
            matched = [p for p in paras if matches(p, keywords, args.strict)]
            if not matched:
                matched = [p for p in paras if matches(p, keywords, False)]
            print(f"\n[{i}] {it['title']} — {it.get('center')}")
            if not paras:
                print("    (تعذر استخراج فقرات نصية — الصفحة قد تكون جافاسكريبت)")
            for p in matched[:2]:
                snippet = p[:400]
                frag = urllib.parse.quote(snippet[:250])
                hl = f"{it['link']}#:~:text={frag}"
                print(f"    ⚡ Copy link to highlight: {hl}")
                print(f"       النص: {snippet[:220]}...")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
