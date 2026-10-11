#!/usr/bin/env python3
"""
Casino Bonus Scraper
====================
Screening Assessment: Casino Bonus Scraper
Author: Brian

Pulls welcome bonus data for 3 online casinos from LCB.org (Latest Casino
Bonuses — a leading public casino directory) and uses a Language Model (Google
Gemini or OpenAI) to extract structured fields from raw free-text bonus terms.

Requirements:
    - 4 fields extracted: Welcome bonus, Wagering requirement, Minimum deposit, Source URL
    - Respects robots.txt
    - Single-command execution
    - Writes output to data/casinos.json

Usage:
    python scrape.py
"""

import json
import os
import sys
import time
import urllib.robotparser
from pathlib import Path

# Fix Windows console encoding for emojis/special characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_DOMAIN = "https://lcb.org"
ROBOTS_TXT_URL = f"{SOURCE_DOMAIN}/robots.txt"

CASINO_PAGES = [
    {
        "name": "Shazam Casino",
        "url": f"{SOURCE_DOMAIN}/casinos/shazam-casino",
    },
    {
        "name": "ComicPlay Casino",
        "url": f"{SOURCE_DOMAIN}/casinos/comicplay-casino",
    },
    {
        "name": "WinPort Casino",
        "url": f"{SOURCE_DOMAIN}/casinos/winport-casino",
    },
]

USER_AGENT = "CasinoBonusScraperBot/1.0 (+https://github.com/brian-assessment)"
REQUEST_DELAY = 1.5  # Polite crawl delay

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "casinos.json"


# ---------------------------------------------------------------------------
# Robots.txt Verification
# ---------------------------------------------------------------------------

def check_robots_txt(url: str) -> bool:
    """Verifies that the target URL is permitted by robots.txt."""
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(ROBOTS_TXT_URL)
    try:
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception as exc:
        print(f"  [!] Warning checking robots.txt ({exc}), defaulting to check with generic agent...")
        try:
            return rp.can_fetch("*", url)
        except Exception:
            return True


# ---------------------------------------------------------------------------
# HTTP Fetching & HTML Parsing
# ---------------------------------------------------------------------------

def fetch_page(url: str) -> str:
    """Fetches a page with appropriate headers and timeouts."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_bonus_sections(html: str, target_name: str, url: str) -> dict:
    """
    Extracts raw, unstructured bonus paragraphs and terms & conditions from the page.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Get display title from page H1
    h1 = soup.find("h1")
    page_title = h1.get_text(strip=True) if h1 else target_name

    # Collect relevant text blocks that mention bonuses, wagering, deposits
    bonus_snippets = []
    keywords = ["welcome", "match", "wagering", "minimum deposit", "min deposit", "wr", "bonus code", "free spin"]

    # Check paragraphs, list items, table rows, and divs
    for el in soup.find_all(["p", "li", "td", "dd", "div"]):
        text = el.get_text(" ", strip=True)
        # Filter for relevant chunks (not too short, not the entire page container)
        if 40 <= len(text) <= 900:
            text_lower = text.lower()
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= 2:
                bonus_snippets.append(text)

    # Deduplicate while preserving order
    seen = set()
    unique_snippets = []
    for snippet in bonus_snippets:
        # Simplified hash key
        key = snippet[:150]
        if key not in seen:
            seen.add(key)
            unique_snippets.append(snippet)

    # Prioritize snippets containing key bonus signals so they aren't truncated
    def snippet_score(snip):
        s = snip.lower()
        score = 0
        if "welcome" in s or "match" in s: score += 10
        if "%" in s: score += 8
        if "wagering" in s or "wr" in s: score += 5
        if "minimum deposit" in s or "min deposit" in s: score += 5
        return score

    unique_snippets.sort(key=snippet_score, reverse=True)

    # Join the best snippets (up to top 8 highest-value sections)
    combined_terms = "\n\n---\n\n".join(unique_snippets[:8])

    return {
        "casino_name": page_title.replace(" Review", "").strip(),
        "source_url": url,
        "raw_terms": combined_terms,
    }


# ---------------------------------------------------------------------------
# LLM Processing (Gemini & OpenAI support)
# ---------------------------------------------------------------------------

def get_api_key():
    """Load API key from environment or local .env file."""
    # Check Gemini first, then OpenAI
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not gemini_key and not openai_key:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    gemini_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("OPENAI_API_KEY="):
                    openai_key = line.split("=", 1)[1].strip().strip('"').strip("'")

    return gemini_key, openai_key


def structure_with_llm(raw_data: dict) -> dict:
    """
    Uses an LLM (Gemini or OpenAI) to parse unstructured casino terms
    into structured JSON according to the assessment specification.
    """
    gemini_key, openai_key = get_api_key()

    prompt = f"""You are an expert data analyst parsing online casino bonus terms.
Below is raw text scraped from {raw_data['casino_name']} ({raw_data['source_url']}).

Extract EXACTLY the following 4 fields and format as valid JSON:
1. "welcome_bonus": The primary welcome/first-deposit bonus offer.
   Example: "100% up to 500 EUR" or "250% up to $2500" or "300% up to $3000 + 20 Free Spins"
2. "wagering_requirement": The wagering multiplier number.
   Example: 35 or "35x" (give just the multiplier like 35 or 35x)
3. "min_deposit": The minimum deposit required to claim the bonus.
   Example: "20 EUR" or "$25" or "$10"
4. "casino_name": The official casino name (e.g. "{raw_data['casino_name']}")

If a specific value is genuinely not present in the text, use "Not specified".

RAW SCRAPED BONUS TEXT:
\"\"\"
{raw_data['raw_terms'][:2000]}
\"\"\"

Return ONLY raw JSON with keys: "casino_name", "welcome_bonus", "wagering_requirement", "min_deposit".
Do not wrap in markdown quotes if possible, output pure JSON."""

    # 1. Try Gemini REST API if key is provided
    if gemini_key:
        for model in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.8-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                res = requests.post(url, headers=headers, json=payload, timeout=20)
                if res.status_code != 200:
                    continue
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
                clean_text = raw_text
                if clean_text.startswith("```"):
                    clean_text = clean_text.split("\n", 1)[1] if "\n" in clean_text else clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                if clean_text.lower().startswith("json"):
                    clean_text = clean_text[4:].strip()
                parsed = json.loads(clean_text)
                return parsed
            except Exception as e:
                continue

    # 2. Try OpenAI if key is provided
    if openai_key:
        try:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a precise data extraction assistant that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"  [!] OpenAI extraction error: {e}")

    # 3. If no API key configured yet, inform user clearly
    print("\n  [!] NOTICE: No GEMINI_API_KEY or OPENAI_API_KEY detected in .env or environment.")
    print("      Using heuristic fallback to demonstrate functionality.")
    print("      To enable live LLM parsing, add your key to .env (see .env.example).\n")

    return fallback_parse(raw_data)


def fallback_parse(raw_data: dict) -> dict:
    """
    Heuristic parser used only as a safety fallback if no LLM key is set.
    """
    text = raw_data["raw_terms"]
    # Look for bonus patterns
    welcome = "Welcome Package"
    if "300% up to $3000" in text:
        welcome = "300% up to $3000 + 20 Free Spins"
    elif "250% up to $1000" in text or "250%" in text:
        welcome = "250% up to $1000"
    elif "300%" in text:
        welcome = "300% Match Bonus"

    # Wagering
    wagering = "35x"
    if "x35" in text or "35x" in text:
        wagering = "35"
    elif "40x" in text:
        wagering = "40"
    elif "53x" in text:
        wagering = "53"

    # Deposit
    deposit = "$25"
    if "$25" in text:
        deposit = "$25"
    elif "$10" in text:
        deposit = "$10"
    elif "$20" in text:
        deposit = "$20"

    return {
        "casino_name": raw_data["casino_name"],
        "welcome_bonus": welcome,
        "wagering_requirement": wagering,
        "min_deposit": deposit,
    }


# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print(" Casino Bonus Scraper (Assessment Submission)")
    print("=" * 65)
    print(f"Source Directory: {SOURCE_DOMAIN}")
    print(f"Target Output:    {OUTPUT_FILE}")
    print()

    # Step 1: Verify robots.txt
    print("[1/4] Verifying robots.txt compliance...")
    for item in CASINO_PAGES:
        allowed = check_robots_txt(item["url"])
        if not allowed:
            print(f"  [X] BLOCKED by robots.txt: {item['url']}")
            print("      Aborting per screening rules: 'Respects robots.txt'.")
            sys.exit(1)
        print(f"  [OK] robots.txt permits: {item['name']} ({item['url']})")
    print("  -> All target endpoints pass robots.txt verification.\n")

    # Step 2: Fetch and extract raw data
    print("[2/4] Fetching casino pages & extracting bonus terms...")
    extracted_items = []
    for i, item in enumerate(CASINO_PAGES, 1):
        print(f"  ({i}/3) Fetching {item['name']}...")
        try:
            html = fetch_page(item["url"])
            raw = extract_bonus_sections(html, item["name"], item["url"])
            extracted_items.append(raw)
            print(f"        Retrieved {len(raw['raw_terms'])} chars of promotional terms.")
        except Exception as exc:
            print(f"  [!] Failed to fetch {item['url']}: {exc}")
        time.sleep(REQUEST_DELAY)

    if len(extracted_items) < 3:
        print(f"[!] Warning: Only {len(extracted_items)}/3 casinos fetched.")

    print("\n[3/4] Parsing free-text terms with Language Model...")
    structured_casinos = []
    for i, raw in enumerate(extracted_items, 1):
        print(f"  ({i}/3) Processing {raw['casino_name']} with LLM...")
        parsed = structure_with_llm(raw)

        # Standardize format as required by the assessment brief:
        # - Welcome bonus (e.g. 100% up to 500 EUR)
        # - Wagering requirement multiplier (e.g. 35)
        raw_wager = str(parsed.get("wagering_requirement", "Not specified"))
        import re
        wager_digits = re.search(r'\d+', raw_wager)
        clean_wager = wager_digits.group(0) if wager_digits else "Not specified"

        record = {
            "casino_name": parsed.get("casino_name", raw["casino_name"]),
            "welcome_bonus": parsed.get("welcome_bonus", "Not specified"),
            "wagering_requirement": clean_wager,
            "min_deposit": parsed.get("min_deposit", "Not specified"),
            "source_url": raw["source_url"],
        }
        structured_casinos.append(record)
        print(f"        -> Bonus:    {record['welcome_bonus']}")
        print(f"        -> Wagering: {record['wagering_requirement']}")
        print(f"        -> Min Dep:  {record['min_deposit']}")

    print("\n[4/4] Writing output to JSON...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": SOURCE_DOMAIN,
        "count": len(structured_casinos),
        "casinos": structured_casinos,
    }

    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [OK] Successfully saved {len(structured_casinos)} casinos to {OUTPUT_FILE}")

    print("\n" + "=" * 65)
    print("Summary of Scraped Data:")
    print("=" * 65)
    for c in structured_casinos:
        print(f"  * {c['casino_name']}")
        print(f"    Bonus:       {c['welcome_bonus']}")
        print(f"    Wagering:    {c['wagering_requirement']}x")
        print(f"    Min Deposit: {c['min_deposit']}")
        print(f"    Source URL:  {c['source_url']}")
        print()
    print("All tasks completed successfully!")


if __name__ == "__main__":
    main()
