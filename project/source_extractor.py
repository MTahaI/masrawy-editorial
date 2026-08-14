#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
source_extractor.py — يستخرج نص نظيف + ميتاداتا من أي رابط
الاستخدام:
    python source_extractor.py <URL> [--format json] [--timeout 45]

سلسلة الفتح (حسب التحقق_المصادري.md):
1. tavily-extract (أساسي) — يعمل مع معظم المواقع
2. webfetch (احتياط) — صفحات ثابتة
3. puppeteer (مواقع سعودية JS: spa.gov.sa, rcmc.gov.sa, haj.gov.sa, discovermakkah.sa, my.gov.sa, gov.sa)

المخرج (JSON):
{
  "title": "...",
  "date": "...",
  "author": "...",
  "site_name": "...",
  "domain": "...",
  "text": "...",
  "url": "...",
  "extraction_method": "tavily|webfetch|puppeteer"
}
"""

import sys
import json
import argparse
import re
import io
from urllib.parse import urlparse
from typing import Optional, Dict, Any

# Force UTF-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---- التحقق من المكتبات ----
try:
    import requests
except ImportError:
    print(json.dumps({"error": "مكتبة requests غير مثبتة. ثبت: pip install requests"}, ensure_ascii=False))
    sys.exit(1)

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

# ---- قائمة النطاقات السعودية الرسمية التي تحتاج Puppeteer ----
SAUDI_OFFICIAL_DOMAINS = {
    "spa.gov.sa",
    "rcmc.gov.sa",
    "haj.gov.sa",
    "discovermakkah.sa",
    "my.gov.sa",
    "gov.sa",
    "www.spa.gov.sa",
    "www.rcmc.gov.sa",
    "www.haj.gov.sa",
    "www.discovermakkah.sa",
    "www.my.gov.sa",
    "www.gov.sa",
}

def get_domain(url: str) -> str:
    """استخراج النطاق من الرابط"""
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")

def is_saudi_official(url: str) -> bool:
    """فحص ما إذا كان الرابط لموقع سعودي رسمي يحتاج Puppeteer"""
    domain = get_domain(url)
    return domain in SAUDI_OFFICIAL_DOMAINS

def extract_via_tavily(url: str, timeout: int = 45) -> Optional[Dict[str, Any]]:
    """محاولة الاستخراج عبر Tavily"""
    if TavilyClient is None:
        return None
    try:
        import os
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return None
        client = TavilyClient(api_key=api_key)
        result = client.extract(urls=[url], extract_depth="advanced", format="markdown")
        if result and "results" in result and result["results"]:
            r = result["results"][0]
            return {
                "title": r.get("title", ""),
                "date": r.get("published_date", ""),
                "author": r.get("author", ""),
                "site_name": r.get("site_name", ""),
                "domain": get_domain(url),
                "text": r.get("content", ""),
                "url": url,
                "extraction_method": "tavily"
            }
    except Exception:
        pass
    return None

def extract_via_webfetch(url: str, timeout: int = 45) -> Optional[Dict[str, Any]]:
    """محاولة الاستخراج عبر webfetch (HTTP بسيط)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
        # استخراج بسيط للعنوان والنص (بدون مكتبات ثقيلة)
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""
        # إزالة السكريبتات والأنماط
        clean_html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r"<style[^>]*>.*?</style>", "", clean_html, flags=re.DOTALL | re.IGNORECASE)
        # استخراج النص من الفقرات
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", clean_html, flags=re.DOTALL | re.IGNORECASE)
        text = "\n\n".join(re.sub(r"<[^>]+>", "", p).strip() for p in paragraphs if p.strip())
        if not text:
            # محاولة بديلة: نص الجسم كاملًا
            body_match = re.search(r"<body[^>]*>(.*?)</body>", clean_html, flags=re.DOTALL | re.IGNORECASE)
            if body_match:
                text = re.sub(r"<[^>]+>", "", body_match.group(1)).strip()
        return {
            "title": title,
            "date": "",
            "author": "",
            "site_name": "",
            "domain": get_domain(url),
            "text": text[:50000],  # حد أقصى 50K حرف
            "url": url,
            "extraction_method": "webfetch"
        }
    except Exception:
        return None

def extract_via_puppeteer(url: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
    """محاولة الاستخراج عبر Puppeteer (للمواقع السعودية JS)"""
    # نستخدم الأمر عبر subprocess لاستدعاء Node/Puppeteer
    # ملاحظة: هذا يتطلب توفر Node.js و puppeteer محليًا
    # كبديل، نعيد None ليدل على عدم توفر الأداة
    # في البيئة الفعلية، يمكن استدعاء puppeteer عبر MCP أو سكربت Node منفصل
    return None

def extract_source(url: str, timeout: int = 45) -> Dict[str, Any]:
    """الدالة الرئيسية: تحاول السلسلة كاملة"""
    # 1. Tavily (الأفضل للنظافة)
    result = extract_via_tavily(url, timeout)
    if result and result["text"].strip():
        return result

    # 2. Webfetch (احتياط للصفحات الثابتة)
    result = extract_via_webfetch(url, timeout)
    if result and result["text"].strip():
        return result

    # 3. Puppeteer (للمواقع السعودية الرسمية)
    if is_saudi_official(url):
        result = extract_via_puppeteer(url, timeout)
        if result and result["text"].strip():
            return result

    # فشل كامل
    return {
        "title": "",
        "date": "",
        "author": "",
        "site_name": "",
        "domain": get_domain(url),
        "text": "",
        "url": url,
        "extraction_method": "failed",
        "error": "فشل الاستخراج من جميع المصادر"
    }

def main():
    parser = argparse.ArgumentParser(description="Extract clean text from a URL")
    parser.add_argument("url", help="URL to extract")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--timeout", type=int, default=45, help="Timeout in seconds")
    args = parser.parse_args()

    result = extract_source(args.url, args.timeout)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Title: {result['title']}")
        print(f"Domain: {result['domain']}")
        print(f"Method: {result['extraction_method']}")
        print(f"Text ({len(result['text'])} chars):")
        print(result['text'][:3000])
        if len(result['text']) > 3000:
            print("... (truncated)")

    # رمز الخروج: 0 نجاح، 1 فشل
    sys.exit(0 if result["extraction_method"] != "failed" else 1)

if __name__ == "__main__":
    main()