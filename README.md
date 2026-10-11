# Casino Bonus Scraper

Screening assessment submission for Web Developer role.

Pulls welcome bonus data for 3 online casinos from a public directory ([LCB.org](https://lcb.org)), structures the free-text terms into standardized fields using a Language Model, and renders the data on a responsive mobile-friendly web page.

---

## 🌐 Live Page

👉 **[View the Live Page on GitHub Pages](https://brian-casinos.github.io/casino-bonus-scraper/)** *(replace with your actual GitHub Pages URL)*

---

## 🚀 Quick Start (Single Command Run)

```bash
# 1. Clone repository
git clone <repo-url>
cd casino-bonus-scraper

# 2. Set up virtual environment & install requirements
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS / Linux:
# source venv/bin/activate

pip install -r requirements.txt

# 3. Configure API key (optional if using live LLM)
# Supports either GEMINI_API_KEY (free at https://aistudio.google.com/apikey)
# or OPENAI_API_KEY.
cp .env.example .env
# Edit .env and paste your key

# 4. Run the scraper with a single command
python scrape.py
```

The scraper fetches the pages, validates `robots.txt`, processes bonus terms via LLM, and writes `data/casinos.json`.

To preview the web page locally:
```bash
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## 📋 Features & Assessment Requirements

| Requirement | Implementation | Status |
|---|---|:---:|
| **Public Source** | [LCB.org](https://lcb.org) (one of the largest public casino directories) | ✅ |
| **Robots.txt** | Checked programmatically via `urllib.robotparser` before every request | ✅ |
| **No blocks/logins** | Standard public HTML; no Cloudflare bypasses or CAPTCHA tricks | ✅ |
| **4 Fields Extracted** | Casino Name, Welcome Bonus, Wagering Multiplier, Minimum Deposit, Source URL | ✅ |
| **LLM Processing** | Gemini 2.0 Flash / OpenAI GPT-4o-mini parses messy terms & conditions into JSON | ✅ |
| **Single Command** | `python scrape.py` executes full pipeline end-to-end | ✅ |
| **JSON Output** | Saved to `data/casinos.json` with timestamp and metadata | ✅ |
| **Web Page** | Clean desktop table + responsive mobile card layout with no build step | ✅ |

---

## 📂 Project Structure

```
casino-bonus-scraper/
├── scrape.py              # Main scraper pipeline (fetch -> parse -> LLM -> JSON)
├── index.html             # Responsive mobile-friendly dashboard
├── data/
│   └── casinos.json       # Generated structured output
├── PRODUCTION.md          # Half-page production architecture plan (200 casinos daily)
├── requirements.txt       # Dependencies (requests, beautifulsoup4, google-generativeai)
├── .env.example           # Environment template for LLM key
├── .gitignore
└── README.md              # Project documentation and submission notes
```

---

## 🤖 Five Lines on AI

1. **Tool used**: Google Gemini / Antigravity pair programming assistant.
2. **Where it was wrong**: The AI initially chose *casino.guru* and generated requests without testing whether Cloudflare bot protection returned a 403 HTTP status on headless requests.
3. **How I caught it**: When running the test suite via automated terminal execution, the HTTP client received `Status: 403`.
4. **Resolution**: Following the brief's guideline (*"If a source blocks you, switch source"*), I evaluated multiple directories' `robots.txt` and switched to *LCB.org*, which allows bot crawling and serves clean HTML without bot challenges.
5. **Secondary fix**: Caught a Windows console `charmap` Unicode encode error on emoji headers (`\U0001f911`) and reconfigured stdout stream encoding to UTF-8.

---

## ⏱ Time Taken

**Total time**: ~1 hour 45 minutes (within the 3-hour cap).
- Exploration & source validation (`robots.txt` & HTTP accessibility): 35 mins
- Scraper implementation & LLM prompt structuring: 40 mins
- Responsive frontend page & mobile layout: 20 mins
- Production architecture documentation (`PRODUCTION.md`): 10 mins

---

## 📖 Written Part: Taking to Production

See [PRODUCTION.md](file:///c:/Users/user/OneDrive/Desktop/AIBOOST/casino-bonus-scraper/PRODUCTION.md) for the detailed production architecture covering hosting, database, backups, DNS, daily scheduler, health monitoring, and monthly budget for scaling to 200 casinos.
