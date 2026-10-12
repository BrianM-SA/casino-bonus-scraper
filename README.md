# Casino Bonus Scraper

A lightweight Python scraper that extracts welcome bonus data for 3 online casinos from [LCB.org](https://lcb.org), parses promotional terms into structured fields using a Language Model (Google Gemini), and displays the results on a responsive web page.

---

## Live Demo

👉 **[Live Page](https://brianm-sa.github.io/casino-bonus-scraper/)**

---

## Setup & Running

### 1. Installation

```bash
# Clone repository
git clone https://github.com/BrianM-SA/casino-bonus-scraper.git
cd casino-bonus-scraper

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Add your Gemini API key (free at [Google AI Studio](https://aistudio.google.com/apikey)):

```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Run the Scraper

Run the scraper with a single command:

```bash
python scrape.py
```

This will:
1. Verify `robots.txt` permissions for each URL.
2. Fetch the casino promotional pages.
3. Send raw terms to the LLM to extract structured fields.
4. Save the output to `data/casinos.json`.

### 4. View the Web Page

Start a local server:

```bash
python -m http.server 8080
```

Open `http://localhost:8080` in your browser.

---

## Project Structure

```
casino-bonus-scraper/
├── scrape.py              # Scraper script (fetch -> extract -> LLM parse -> JSON)
├── index.html             # Responsive frontend table/card dashboard
├── data/
│   └── casinos.json       # Scraped dataset
├── PRODUCTION.md          # Architecture notes on scaling to 200 casinos daily
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── README.md
```

---

## Implementation Notes

- **Source Selection**: Selected LCB.org as the public directory. It provides detailed bonus terms, permits crawling under `robots.txt`, and serves server-rendered HTML without anti-bot blocks.
- **LLM Extraction**: Casino bonus terms vary widely in phrasing (match percentages, maximum amounts, free spin combinations, rollover rules). Rather than brittle regex, Gemini parses the raw text into four normalized fields:
  - Welcome bonus
  - Wagering multiplier
  - Minimum deposit
  - Source URL
- **Frontend**: Plain HTML, CSS, and JavaScript with zero build tools or external UI frameworks. Uses a table layout on desktop and switches to a card layout on mobile screens.
- **Production Scaling**: See [PRODUCTION.md](PRODUCTION.md) for details on taking this pipeline to 200 casinos updated daily.
