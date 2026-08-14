#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
news_search.py — رادار البحث الإخباري العربي (Google News RSS)
===============================================================
بحث فوري في أخبار Google News بلا أي مفتاح، مع فك روابط التوجيه
للوصول إلى المصدر الأصلي. مصمم للبيئة التحريرية: خفيف، يُستدعى
عند الطلب فقط (لا سيرفر دائم، لا مفاتيح، لا تثبيت).

الاستخدام:
  python news_search.py --query "مجلس الوزراء السعودي" [--region sa|eg|wt] [--lang ar|en] [--max 10] [--resolve]

المخرجات: عنوان الخبر | المصدر (المنفذ) | التاريخ | الرابط النهائي
"""
import argparse, html, json, re, sys, urllib.parse, urllib.request

def fetch_rss(query: str, region: str = "sa", lang: str = "ar", max_items: int = 10) -> list:
    params = {"q": query, "hl": lang, "gl": region, "ceid": f"{region}:{lang}"}
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        xml = resp.read().decode("utf-8", "ignore")
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    out = []
    for it in items[:max_items]:
        title = re.search(r"<title>(.*?)</title>", it, re.S)
        link = re.search(r"<link>(.*?)</link>", it, re.S)
        date = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
        src = re.search(r'<source[^>]*url="([^"]*)"[^>]*>(.*?)</source>', it, re.S)
        out.append({
            "title": html.unescape(title.group(1).strip()) if title else "",
            "link": link.group(1).strip() if link else "",
            "date": date.group(1).strip() if date else "",
            "source_name": html.unescape(src.group(2).strip()) if src else "",
            "source_url": src.group(1).strip() if src else "",
        })
    return out

def resolve_link(link: str) -> str:
    """فك توجيه Google News للوصول للمصدر الأصلي (بدون جلب الصفحة)."""
    if "news.google.com" not in link:
        return link
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise StopIteration(newurl)
    try:
        opener = urllib.request.build_opener(NoRedirect)
        opener.open(urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"}), timeout=15)
    except StopIteration as e:
        return str(e)
    except Exception:
        pass
    return link  # تعذر الفك — يعرض رابط Google News كما هو

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--region", default="sa", help="sa | eg | wt")
    ap.add_argument("--lang", default="ar", help="ar | en")
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--resolve", action="store_true", help="فك روابط Google News إلى المصدر الأصلي")
    args = ap.parse_args()

    items = fetch_rss(args.query, args.region, args.lang, args.max)
    if not items:
        print(json.dumps({"error": "no results", "query": args.query}, ensure_ascii=False))
        return
    for it in items:
        link = resolve_link(it["link"]) if args.resolve else it["link"]
        print(f"{it['title']}")
        print(f"  المصدر: {it['source_name']} | {it['date']}")
        print(f"  الرابط: {link}")
        print()

if __name__ == "__main__":
    main()
