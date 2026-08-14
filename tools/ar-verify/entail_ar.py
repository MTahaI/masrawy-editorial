#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entail_ar.py — أداة التحقق العربي (الاستلزام) لبيئة التحرير
============================================================
مستويان:
  1) heuristic محلي (فوري، بلا مفاتيح): تطبيع عربي + مطابقة كلمات + كشف اقتباس حرفي.
  2) حكم دلالي عبر Gemini (اختياري --llm): يفهم المعنى لا الحروف.

الاستخدام:
  python entail_ar.py --claim "..." --source-text "..." [--llm gemini] [--verbose]
  python entail_ar.py --claim "..." --source-url "https://..." [--llm gemini]
"""
import argparse, json, re, sys, time, unicodedata, urllib.request

# ---------- التطبيع العربي ----------
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u0652\u0670]')          # الحركات
ARABIC_HAMZA = str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ؤ':'و','ئ':'ي'})
TAA_MARBUTA = str.maketrans({'ة':'ه'})
ALEF_MAQSURA = str.maketrans({'ى':'ي'})
PUNCT = re.compile(r'[\u060C\u061B\u061F\u0640\u0660-\u0669\u200c-\u200f\s\W_]+')
STOP_AR = set("""في من على إلى عن أن إن كان كانت هذا هذه ذلك التي الذي ما لا وقد لم لن
بعد قبل عند كل بعض غير بين مع كما حيث حتى منذ منذ يوم جدة الرياض""".split())

def normalize_ar(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    text = ARABIC_DIACRITICS.sub('', text)
    text = text.translate(ARABIC_HAMZA).translate(TAA_MARBUTA).translate(ALEF_MAQSURA)
    text = PUNCT.sub(' ', text)
    return ' '.join(text.split()).strip()

def tokens(text: str) -> list:
    return normalize_ar(text).split()

# ---------- الفحص الحرفي (heuristic عربي) ----------
def lexical_entail(claim: str, source: str) -> dict:
    c_tok, s_tok = tokens(claim), tokens(source)
    if not c_tok:
        return {"status": "UNSUPPORTED", "score": 0.0, "reason": "claim empty after normalization"}
    c_set, s_set = set(c_tok), set(s_tok)
    overlap = sum(1 for w in c_tok if w in s_set)
    # ترجيح: الكلمات التي ليست وقفًا عربيًا
    sig_c = [w for w in c_tok if w not in STOP_AR and len(w) > 1]
    sig_hit = sum(1 for w in sig_c if w in s_set)
    score = sig_hit / len(sig_c) if sig_c else overlap / len(c_tok)
    # كشف اقتباس حرفي (تسلسل 4+ كلمات متتالية بعد التطبيع)
    exact = ""
    for start in range(len(s_tok) - 3):
        for ln in range(8, 3, -1):
            seq = ' '.join(s_tok[start:start + ln])
            if seq in ' '.join(c_tok):
                exact = seq
                break
        if exact:
            break
    if exact and len(exact.split()) >= 4:
        return {"status": "SUPPORTED", "score": round(min(1.0, 0.6 + 0.08 * len(exact.split())), 3),
                "reason": f"literal sequence ({len(exact.split())} words) found in source", "evidence": exact}
    if score >= 0.85:
        return {"status": "SUPPORTED", "score": round(score, 3), "reason": "high word overlap after Arabic normalization"}
    if score >= 0.55:
        return {"status": "PARTIAL", "score": round(score, 3), "reason": "moderate overlap — verify manually"}
    return {"status": "UNSUPPORTED", "score": round(score, 3), "reason": "low overlap"}

# ---------- الحكم الدلالي عبر Gemini ----------
def gemini_verdict(claim: str, source: str) -> dict:
    import os
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return {"error": "GEMINI_API_KEY not set"}
    prompt = (
        "أنت مدقق استلزام (entailment) صارم للنصوص العربية الصحفية.\n"
        "حكم على: هل الادعاء مدعوم حرفيًا أو دلاليًا من نص المصدر؟ لا تخمّن معلومات خارج النص.\n"
        f"الادعاء: {claim}\n"
        f"نص المصدر: {source}\n"
        "أجب JSON فقط بالشكل: {\"status\": \"SUPPORTED|PARTIAL|UNSUPPORTED\", \"score\": 0.0-1.0, \"reason\": \"...\"}"
    )
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            m = re.search(r'\{.*\}', text, re.S)
            if m:
                return json.loads(m.group(0))
            return {"error": "non-JSON model output", "raw": text[:200]}
        except Exception as e:
            if attempt == 2 or "503" not in str(e):
                return {"error": str(e)}
            time.sleep(6 * (attempt + 1))

# ---------- الجلب من URL ----------
def fetch_text(url: str, max_chars: int = 12000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except Exception as e:
        return f"__FETCH_ERROR__: {e}"
    m = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I)
    title = m.group(1).strip() if m else ""
    text = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', raw)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return f"{title} {text}"[:max_chars]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", required=True)
    ap.add_argument("--source-text", default="")
    ap.add_argument("--source-url", default="")
    ap.add_argument("--llm", choices=["gemini", "none"], default="none")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    source = args.source_text
    if args.source_url and not source:
        source = fetch_text(args.source_url)
        if source.startswith("__FETCH_ERROR__"):
            print(json.dumps({"error": source}, ensure_ascii=False))
            return

    out = {"claim": args.claim, "lexical": lexical_entail(args.claim, source)}
    if args.llm == "gemini":
        out["semantic"] = gemini_verdict(args.claim, source)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
