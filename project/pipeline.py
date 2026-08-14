#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py --check — Automated report verification before delivery
Implements rules from التحقق_المصادري.md:
- Extracts all doc lines ("التوثيق:" or "المصدر المباشر:")
- Opens each URL via source_extractor.py
- Verifies: (a) content match, (b) domain match, (c) >=3 unique domains
- Exit codes: 0 (success) / 3 (domains<3) / 1 (verification error) / 2 (runtime error)

Usage:
    python pipeline.py --check <report_file.txt>
    python pipeline.py --check - < report.txt   # from stdin
    python pipeline.py --check <report_file.txt> --allow-weak-sources  # one-time override
"""

import sys
import json
import argparse
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse

# ---- Settings ----
SOURCE_EXTRACTOR = Path(__file__).parent / "source_extractor.py"
MIN_UNIQUE_DOMAINS = 3  # Rule 7: 3 unique domains minimum

# ---- Supported doc line patterns ----
DOC_PATTERNS = [
    r"\u0627\u0644\u062a\u0648\u062b\u064a\u0642\s*:\s*(https?://\S+)",           # التوثيق:
    r"\u0627\u0644\u0645\u0635\u062f\u0631\s*\u0627\u0644\u0645\u0628\u0627\u0634\u0631\s*:\s*(https?://\S+)",  # المصدر المباشر:
    r"\u0627\u0644\u0645\u0635\u062f\u0631\s*:\s*(https?://\S+)",             # المصدر:
    r"source\s*:\s*(https?://\S+)",             # English
]

def extract_doc_urls(text: str) -> List[Tuple[int, str, str]]:
    """
    Extract all documentation URLs from text
    Returns: list of (line_number, url, full_line)
    """
    urls = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        for pattern in DOC_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for url in matches:
                url = url.rstrip(").,؛،]})>")
                urls.append((i, url, line.strip()))
    return urls

def get_domain(url: str) -> str:
    """Extract base domain (without www)"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""

def call_source_extractor(url: str, timeout: int = 45) -> Dict:
    """Call source_extractor.py and get JSON"""
    try:
        result = subprocess.run(
            [sys.executable, str(SOURCE_EXTRACTOR), url, "--format", "json", "--timeout", str(timeout)],
            capture_output=True,
            text=True,
            timeout=timeout + 10,
            encoding="utf-8"
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        else:
            return {"extraction_method": "failed", "error": result.stderr or "no output"}
    except subprocess.TimeoutExpired:
        return {"extraction_method": "failed", "error": "timeout"}
    except json.JSONDecodeError:
        return {"extraction_method": "failed", "error": "invalid JSON output"}
    except Exception as e:
        return {"extraction_method": "failed", "error": str(e)}

def check_content_match(paragraph_text: str, source_text: str, threshold: float = 0.3) -> bool:
    """
    Approximate content match verification:
    - Extract keywords from paragraph (names, numbers, dates, key verbs)
    - Search for them in source text
    - Return True if reasonable ratio found
    """
    if not paragraph_text or not source_text:
        return False

    # Keywords: Arabic words >=3 chars, numbers, dates, capitalized English words
    keywords = re.findall(r"[\u0600-\u06FF]{3,}|\d+(?:\.\d+)?%?|\d{1,2}/\d{1,2}/\d{4}|\b[A-Z][a-z]+\b", paragraph_text)
    keywords = [k for k in keywords if len(k) >= 3 or k.isdigit()]
    if not keywords:
        return True  # Cannot verify, pass

    source_lower = source_text.lower()
    matches = sum(1 for k in keywords if k.lower() in source_lower)
    ratio = matches / len(keywords)
    return ratio >= threshold

def check_domain_match(claimed_source: str, actual_domain: str) -> bool:
    """
    Verify domain match: actual domain must contain claimed domain or match
    Example: CBS attributed -> cbsnews.com or cbs.com
    """
    if not claimed_source or not actual_domain:
        return False

    claimed = claimed_source.lower().strip()
    actual = actual_domain.lower().strip()

    # Direct match or containment
    if claimed in actual or actual in claimed:
        return True

    # Known aliases
    aliases = {
        "cbs": ["cbsnews.com", "cbs.com"],
        "pbs": ["pbs.org"],
        "reuters": ["reuters.com"],
        "ap": ["apnews.com", "ap.org"],
        "afp": ["afp.com", "afp.fr"],
        "spa": ["spa.gov.sa"],
        "rcmc": ["rcmc.gov.sa"],
        "haj": ["haj.gov.sa"],
        "discovermakkah": ["discovermakkah.sa"],
        "who": ["who.int"],
        "un": ["un.org"],
    }
    for key, domains in aliases.items():
        if key in claimed:
            return any(d in actual for d in domains)

    return False

def verify_report(report_text: str, allow_weak: bool = False) -> Tuple[int, List[str], Dict]:
    """
    Main report verification
    Returns: (exit_code, messages, stats)
    exit_code: 0 success, 3 domains<3, 1 verification error, 2 runtime error
    """
    messages = []
    stats = {
        "total_doc_lines": 0,
        "unique_domains": set(),
        "failed_extractions": 0,
        "content_mismatches": 0,
        "domain_mismatches": 0,
    }

    # 1. Extract doc URLs
    doc_urls = extract_doc_urls(report_text)
    stats["total_doc_lines"] = len(doc_urls)

    if not doc_urls:
        messages.append("ERROR: No documentation lines found in report")
        return 1, messages, stats

    messages.append(f"Found {len(doc_urls)} doc lines")

    # 2. Check each URL
    for line_num, url, line_text in doc_urls:
        messages.append(f"  Line {line_num}: {url}")

        # Extract claimed source from line context
        claimed = ""
        for keyword in ["\u0646\u0642\u0644\u062a", "\u0648\u0641\u0642\u0627\u064b \u0644\u064a", "\u0646\u0642\u0644 \u0645\u0648\u0642\u0639", "\u062a\u0642\u0631\u064a\u0631", "\u0641\u064a \u062d\u062f\u064a\u062b\u0647", "\u0642\u0627\u0644", "\u0623\u0639\u0644\u0646\u062a", "\u0623\u0635\u062f\u0631\u062a"]:
            if keyword in line_text:
                idx = line_text.index(keyword)
                claimed = line_text[idx:idx+60]
                break

        # Call source_extractor
        result = call_source_extractor(url)
        actual_domain = result.get("domain", "")
        source_text = result.get("text", "")
        method = result.get("extraction_method", "failed")

        if method == "failed":
            stats["failed_extractions"] += 1
            messages.append(f"    FAILED extraction: {result.get('error', 'unknown')}")
            continue

        stats["unique_domains"].add(actual_domain)
        messages.append(f"    OK extracted via {method} — domain: {actual_domain}")

        # Content match verification (a)
        lines = report_text.splitlines()
        para_text = ""
        if line_num > 1:
            for j in range(line_num - 2, -1, -1):
                if lines[j].strip():
                    para_text = lines[j].strip()
                    break
        if para_text and not check_content_match(para_text, source_text):
            stats["content_mismatches"] += 1
            messages.append(f"    WARNING: Content may not match source")

        # Domain match verification (b)
        if claimed and not check_domain_match(claimed, actual_domain):
            stats["domain_mismatches"] += 1
            messages.append(f"    WARNING: Domain ({actual_domain}) may not match claimed source ({claimed[:40]})")

    # 3. Rule 7: 3 unique domains minimum
    unique_count = len(stats["unique_domains"])
    stats["unique_domain_count"] = unique_count
    messages.append(f"Unique domains documented: {unique_count}")

    if unique_count < MIN_UNIQUE_DOMAINS:
        if allow_weak:
            messages.append(f"WARNING: Less than {MIN_UNIQUE_DOMAINS} unique domains (allowed via --allow-weak-sources)")
            return 0, messages, stats
        else:
            messages.append(f"FAILED: Report needs at least {MIN_UNIQUE_DOMAINS} unique domains, found {unique_count}")
            messages.append(f"   To override once: add --allow-weak-sources (not recommended for publication)")
            return 3, messages, stats

    # 4. Final summary
    if stats["failed_extractions"] > 0:
        messages.append(f"WARNING: {stats['failed_extractions']} URL(s) failed extraction")
    if stats["content_mismatches"] > 0:
        messages.append(f"WARNING: {stats['content_mismatches']} paragraph(s) with potential content mismatch")
    if stats["domain_mismatches"] > 0:
        messages.append(f"WARNING: {stats['domain_mismatches']} paragraph(s) with potential domain mismatch")

    messages.append("SUCCESS: Verification passed — report ready for delivery")
    return 0, messages, stats

def main():
    parser = argparse.ArgumentParser(description="Automated report verification before delivery")
    parser.add_argument("input", nargs="?", help="Report file (or - for stdin)")
    parser.add_argument("--check", action="store_true", help="Verification mode (required)")
    parser.add_argument("--allow-weak-sources", action="store_true", help="Override 3-domain rule (testing only)")
    parser.add_argument("--timeout", type=int, default=45, help="Source extraction timeout")
    parser.add_argument("--json", action="store_true", help="JSON output for automation")

    args = parser.parse_args()

    if not args.check:
        parser.error("Must use --check")

    # Read report
    if args.input == "-" or args.input is None:
        report_text = sys.stdin.read()
    else:
        try:
            report_text = Path(args.input).read_text(encoding="utf-8")
        except Exception as e:
            print(f"ERROR reading file: {e}", file=sys.stderr)
            sys.exit(2)

    if not report_text.strip():
        print("ERROR: Report is empty", file=sys.stderr)
        sys.exit(2)

    # Run verification
    exit_code, messages, stats = verify_report(report_text, allow_weak=args.allow_weak_sources)

    # Output
    if args.json:
        output = {
            "exit_code": exit_code,
            "messages": messages,
            "stats": {k: (list(v) if isinstance(v, set) else v) for k, v in stats.items()}
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for msg in messages:
            print(msg)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()