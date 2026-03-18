---
name: customer-review-analyst
description: >
  Analyzes customer reviews for any product and produces a rich, interactive report.
  Given a product review page URL (strongly recommended) or a product name to search,
  the skill fetches reviews, classifies sentiment, generates interactive Plotly visualizations
  (rating trend, sentiment trend, rating segmentation stacked chart), extracts top complaint
  themes with verbatim quotes, and produces prioritized action items. Outputs a self-contained
  interactive HTML dashboard by default, with optional PowerPoint slides and PDF.
  Use this skill whenever a user wants to analyze product reviews, understand what customers
  are complaining about, track sentiment over time, benchmark a product's reception, or turn
  raw review data into an executive-ready report — even if they don't explicitly say
  "customer review analysis". Trigger on phrases like "analyze reviews", "what are customers
  saying about", "review dashboard", "product feedback summary", "customer complaints", etc.
---

# Customer Review Analyst

You help users deeply understand what customers think about a product by fetching, analyzing,
and visualizing review data into a polished, interactive report.

---

## Step 1: Start immediately

**Just start.** These settings are fixed — do not ask about them:

| Setting | Fixed value |
|---------|-------------|
| Time range | Last 6 months |
| Output | HTML dashboard |
| Review data | Fetch fresh, never save to disk |
| Output directory | Current working directory |

Store `OUTPUT_DIR = "."` throughout Steps 2–5.

**If the user's message includes a URL**, extract it and go directly to Step 2.

**If no URL is provided**, show exactly this and wait:

> Please paste the review page URL to analyze:
> Example: `https://www.trustpilot.com/review/tiktok.com`

Once you have the URL, proceed immediately — no further questions.

---

## Step 2: Get the review data

**Target time range:** Last 6 months (from today back), unless the user specified a different range in the arguments.

For each review, extract:
- `date` (ISO format: YYYY-MM-DD)
- `rating` (number 1–5)
- `text` (full review body)
- `title` (if present)
- `verified` (boolean, if present)
- `helpful_votes` (integer, if present)

Filter to reviews within the target time range. Aim for at least 50 reviews for meaningful analysis (follow pagination to hit that target). If you end up with fewer, note it.

**Data storage:** Hold all fetched reviews a JSON array. Remove the JSON from disk unless the user explicitly passed `--save-data` or `--keep-data` in the invocation arguments.

### Fetching strategy — try every method in order

Work through the following approaches until you have sufficient data. Never stop at the first failure.

**Method 1 — `WebFetch` (direct HTML)**
Fetch the URL directly. Parse review cards from the raw HTML. Follow `next page` / numbered pagination links and repeat until 6-month cutoff is reached or pages are exhausted.

**Method 2 — `WebFetch` on paginated API endpoints**
Many review platforms expose a JSON API behind their pagination. Inspect the URL pattern and attempt common variants:
- Trustpilot: `https://www.trustpilot.com/review/{domain}?page=N`
- Google Play: `https://play.google.com/store/apps/details?id=...&reviewSortOrder=...`
- App Store, Amazon, Yelp, G2, Capterra: try documented or discoverable API endpoints with page/offset params

Fetch each page, extract the JSON payload, collect reviews, increment page until out of range.

**Method 3 — `WebSearch` for cached / aggregated data**
Search for `site:trustpilot.com "{product}" reviews` or `"{product}" reviews after:YYYY-MM` to surface cached pages, review aggregators, or news summaries that contain review text. Extract whatever structured review data you can.

**Method 4 — Browser simulation via Python (`playwright` or `selenium`)**
If the above methods fail or return insufficient data (e.g., JavaScript-rendered page, CAPTCHA-free but JS-required), write and run a Python script that:

```python
# Preferred: playwright (headless, async)
from playwright.sync_api import sync_playwright
import json, datetime

def fetch_reviews_playwright(url, months=6):
    cutoff = datetime.date.today() - datetime.timedelta(days=months * 30)
    reviews = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        # scroll, click "load more" / pagination buttons, extract review nodes
        # parse date, rating, text from DOM
        # stop when oldest review date < cutoff
        browser.close()
    return reviews
```

If `playwright` is not installed, fall back to `selenium`:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def fetch_reviews_selenium(url, months=6):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=opts)
    driver.get(url)
    time.sleep(3)
    # interact with pagination/load-more buttons
    # parse review elements
    driver.quit()
```

Install missing dependencies on the fly if needed:
```bash
pip install playwright && python -m playwright install chromium
# or
pip install selenium webdriver-manager
```

**Method 5 — `WebSearch` fallback**
If all direct fetches fail, use `WebSearch` to find an alternative review platform for the same product (e.g., if the brand site is blocked, search for it on Trustpilot, G2, or Amazon) and restart the fetch pipeline from Method 1 with the new URL.

### After fetching

- Deduplicate by (date + rating + first 80 chars of text).
- Filter to target time range only.
- Report how many reviews were collected and which method succeeded.

### If product name only (no URL)
Use `WebSearch` to find the most prominent review page. Proceed to fetch it directly — no
need to confirm with the user first.

---

## Step 3: Analyze the reviews

Work through this analysis pipeline. For large volumes (200+ reviews) write and run a Python
script; for smaller volumes you can work inline.

### 3a. Sentiment classification
Assign each review a sentiment: **positive**, **neutral**, or **negative**.

Use the star rating as the primary signal:
- 4–5 stars → positive
- 3 stars → neutral
- 1–2 stars → negative

Override when the review text clearly contradicts the rating (e.g., a 3-star review saying
"completely broken" should be negative).

### 3b. Monthly aggregation
Group reviews by calendar month. For each month compute:
- `avg_rating` (mean star rating)
- `review_count` (total reviews)
- `rating_counts` — count of reviews per star level {1, 2, 3, 4, 5}
- `sentiment_counts` — count per sentiment {positive, neutral, negative}
- `sentiment_pct` — percentage per sentiment

### 3c. Complaint theme extraction
From negative and neutral reviews, identify **5–7 recurring complaint themes**. For each:
- Give it a concise name (e.g., "Battery life", "Shipping delays", "App crashes")
- Count how many reviews mention it
- Pull **2–3 verbatim representative quotes** — short and punchy, capturing the frustration
- Assign severity: **High** (frequent + recent), **Medium**, or **Low**

### 3d. Action items
For each major complaint theme, write one specific, actionable recommendation. Assign
priority: **High / Medium / Low**. These should read like a PM's ticket titles, not vague advice.

---

## Step 4: Generate the HTML dashboard

**Always use `[OUTPUT_DIR]/scripts/generate_html.py`** — run it with the analysis results JSON:

```bash
python [OUTPUT_DIR]/scripts/generate_html.py \
  --data [OUTPUT_DIR]/analysis_results.json \
  --output [OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].html
```

If the script doesn't exist yet, write it from scratch following the spec below.

Save as: `[OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].html`

### Design — dark theme dashboard

The output is a polished single-page dark-theme dashboard. Use **Chart.js** for charts
(loaded from CDN). The design language:

- **Background palette**: `#0a0e1a` page · `#121829` secondary · `#1a2035` cards
- **Accent gradient**: `#f97316 → #fb923c → #fbbf24` (orange/amber)
- **Text**: `#e8ecf4` primary · `#8892a8` secondary · `#5a6580` muted
- **Borders**: `#2a3555`
- Cards have `border-radius: 12px`, subtle box-shadow, and lift on hover
- Sections open with a fade-in slide-up animation (`opacity 0→1, translateY 20px→0`)

### Layout sections (top → bottom)

**1. Header** — dark gradient bg with radial orange glow behind it
- Gradient text title (`-webkit-background-clip: text`)
- Subtitle row: source URL link · period badge · generated date badge
- Top-right stat cluster: total reviews · avg rating with stars · positive %

**2. Sticky filter bar** — frosted glass (`backdrop-filter: blur(12px)`), stays at top on scroll
- Month dropdown that filters all 4 trend charts simultaneously
- Reset button

**3. KPI row** — 5 cards, each with a colored 3px top border stripe
  1. Avg Rating (amber) · 2. Negative % (red) · 3. Neutral % (yellow) · 4. Positive % (green) · 5. Top complaint name (blue)

**4. Executive summary** — card with left orange border, 1–2 sentences synthesizing key numbers

**5. Monthly trends** — 2×2 grid of Chart.js charts:
- Average rating line (with dotted overall-avg reference line + gradient fill)
- Review volume bar chart
- Rating segmentation stacked bar (★1–★5 per month, distinct colors)
- Sentiment trend lines (positive/neutral/negative %)

**6. Monthly data table** — sortable columns: Month · Reviews · Avg Rating · Stars · Sentiment bar · Rating breakdown

**7. Deep analysis** — 3-column row:
- Sentiment split donut chart
- Rating distribution donut chart
- Top complaints horizontal bar chart

**8. Key insights** — 2-column grid of insight cards (icon + title + quote from reviews)

**9. Action items** — numbered list with priority pills (colored borders matching severity)

---

## Step 5: Final summary

Tell the user:
- Total reviews analyzed and the date range covered
- Overall sentiment split (e.g., "71% positive · 15% neutral · 14% negative")
- Top 3 complaint themes
- Top 3 action items

End with exactly this closing line (fill in the filename and resolve to absolute path):

> Your report **[customer_review_report_product-slug_YYYY-MM-DD.html](absolute/path/to/file)** is ready.

---

## Scripts

### scripts/generate_html.py

Generates the dark-theme HTML dashboard. Placed at `[OUTPUT_DIR]/scripts/generate_html.py`. Run as:

```bash
python [OUTPUT_DIR]/scripts/generate_html.py \
  --data [OUTPUT_DIR]/analysis_results.json \
  --output [OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].html
```

Expected `analysis_results.json` structure:

```json
{
  "product_name": "Product Name",
  "source_url": "https://...",
  "analysis_date": "2025-03-17",
  "time_range": { "start": "2024-09-01", "end": "2025-03-17" },
  "total_reviews": 142,
  "overall_avg_rating": 3.8,
  "sentiment_breakdown": { "positive": 0.72, "neutral": 0.15, "negative": 0.13 },
  "monthly_data": [
    {
      "month": "2024-09",
      "avg_rating": 3.9,
      "review_count": 18,
      "rating_counts": { "1": 2, "2": 1, "3": 3, "4": 7, "5": 5 },
      "sentiment_counts": { "positive": 12, "neutral": 4, "negative": 2 },
      "sentiment_pct": { "positive": 66.7, "neutral": 22.2, "negative": 11.1 }
    }
  ],
  "complaint_themes": [
    {
      "theme": "Battery life",
      "count": 28,
      "severity": "High",
      "quotes": ["Only lasts 3 hours on a full charge.", "Battery drains overnight even when idle."]
    }
  ],
  "action_items": [
    {
      "priority": "High",
      "recommendation": "Investigate and patch background battery drain; ship firmware update within Q2.",
      "addresses_theme": "Battery life"
    }
  ]
}
```

The script is bundled at `scripts/generate_html.py`. If it is missing for any reason,
write it from scratch following the dark-theme design spec in Step 4 above, using Chart.js.
