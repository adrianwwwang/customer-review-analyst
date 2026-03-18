---
name: customer-review-analyst
description: >
  Analyzes customer reviews for any product and produces a rich, interactive report.
  Given an exact product review page URL,
  the skill fetches reviews, classifies sentiment, generates interactive Chart.js visualizations
  (rating trend, sentiment trend, rating segmentation stacked chart), extracts top complaint
  themes with verbatim quotes, and produces prioritized action items. Outputs a self-contained
  interactive HTML dashboard by default.
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
| Output directory | Current working directory |

Store `OUTPUT_DIR = "."` throughout Steps 2–5.

**If the user's message includes a URL**, extract it and go directly to Step 2.

**If no URL is provided**, show exactly this and wait:

> Please provide the exact product review page URL to analyze.

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

Filter to reviews within the target time range. Aim for all reviews for meaningful analysis within the time range (follow pagination to hit that target). If you end up with fewer than 50 reviews after filtering, **widen the time range to 12 months and re-fetch before noting the limitation**. If still fewer than 50 after widening, proceed and call out the low sample size prominently in the executive summary.

**Data storage:** Always persist the raw reviews to `[OUTPUT_DIR]/raw_reviews_[product-slug].json` immediately after fetching — before any analysis — so a re-run can skip the network phase. Remove the file at the end unless the user passed `--save-data` or `--keep-data`.

### Fetching strategy — try every method in order

Work through the following approaches until you have sufficient data. Never stop at the first failure.

**Method 1 — `WebFetch` (direct HTML)**
Fetch the URL directly. Parse review cards from the raw HTML. Follow `next page` / numbered pagination links and repeat until 6-month cutoff is reached or pages are exhausted.

**Method 2 — `WebFetch` on paginated API endpoints**
Many review platforms expose a JSON API behind their pagination. Inspect the URL pattern and attempt common variants:
- Trustpilot: `https://www.trustpilot.com/review/{domain}?page=N`
- Google Play: `https://play.google.com/store/apps/details?id=...&reviewSortOrder=...`
- App Store, Amazon, Yelp, G2, Capterra: try documented or discoverable API endpoints with page/offset params

**Tip:** For platforms that support it (Trustpilot, G2, some App Store endpoints), try appending `?count=100` before paginating — some APIs return all records in a single response. Do **not** apply this heuristic blindly to every platform; if the first probe returns the same count as a plain request, the param is ignored and you should switch straight to page-by-page iteration.

**Pagination fast-exit:** After fetching each page, check whether **every item** on the page predates the cutoff. If so, stop immediately without fetching the next page — you have overshot the window. This avoids 1–2 wasteful requests at the boundary.

**Parallel fetching (large datasets):** When the total page count can be estimated from the first response (e.g. total_count header or known page size × first page), use `concurrent.futures.ThreadPoolExecutor(max_workers=5)` to fetch pages in parallel, then merge and sort results by date. This cuts wall-clock fetch time by ~4× on APIs with 20+ pages.

Fetch each page, extract the JSON payload, collect reviews, increment page until out of range.

**Method 3 — `WebSearch` for cached / aggregated data**
Search for `site:trustpilot.com "{product}" reviews` or `"{product}" reviews after:YYYY-MM` to surface cached pages, review aggregators, or news summaries that contain review text. Extract whatever structured review data you can.

**Method 4 — Browser simulation via Python (`playwright` or `selenium`)**
If the above methods fail or return insufficient data (e.g., JavaScript-rendered page, CAPTCHA-free but JS-required), write and run a Python script that:

> **Important:** Always write Python scripts to a file first using `create_file`, then execute with `python3 <path>`. Never use shell heredoc syntax (`<<'PY'`) — it corrupts the terminal session.
> Use a **unique path per run** to avoid `create_file` collisions with leftovers from prior runs. Derive it from the product slug and date, e.g. `/tmp/fetch_reviews_[product-slug].py` and `/tmp/analyze_reviews_[product-slug].py`.

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

### Fetch volume limit

**At every 1,000 reviews collected, check the running total.** When it crosses **5,000 reviews**, pause immediately and ask:

> Fetched **{n} reviews** so far — this is a large dataset.
>
> How would you like to proceed?
> - **A) Stop here** — analyze the {n} reviews already collected (covers the most recent data)
> - **B) Keep going** — increase parallel threads to `max_workers=10` and continue fetching

Wait for the user's reply before continuing. If the user picks **B**, update the thread pool and resume from the last fetched page. If the user picks **A** (or gives no reply within the same turn), proceed to analysis with what has been collected.

### After fetching

- Deduplicate by (date + rating + first 80 chars of text).
- Filter to target time range only.
- **Save raw data immediately** to `[OUTPUT_DIR]/raw_reviews_[product-slug].json` before proceeding to analysis.
- Report how many reviews were collected and which method succeeded.

### If URL is still missing
Do not proceed with search-by-name. Ask the user for the exact product review page URL and wait.

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

Override **only** when the review text contains an explicit negation pattern that directly contradicts the rating:
- Downgrade 4–5 → **negative** only if the text contains a negated problem phrase, e.g. `"doesn't work"`, `"stopped working"`, `"can't connect"`, `"completely broken"`, `"total waste"`. A few incidental negative keywords ("slow", "bug") in an otherwise positive review must **not** trigger a downgrade — require at least one explicit negation (`not`, `never`, `stopped`, `can't`, `won't`) adjacent to a core problem word.
- Upgrade 1–2 → **neutral** only if the text contains strong unambiguous praise with no negation (`"love it"`, `"works great"`, `"amazing"`) and zero problem keywords.
- Leave 3-star reviews as neutral unless a clear majority of the text is either pure praise or pure complaint.

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
- **Deduplicate quotes at this stage** by the first 60 characters of each quote, across all themes — the `generate_html.py` renderer assumes all quotes in `analysis_results.json` are already unique and will not re-deduplicate
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
  --output [OUTPUT_DIR]/[productname]_report_[timestamp].html
```

If the script doesn't exist yet, write it from scratch following the spec below.

Save as: `[OUTPUT_DIR]/[productname]_report_[timestamp].html`

### Design — dark theme dashboard

The output is a polished single-page dark-theme dashboard. Use **Chart.js** for charts
(loaded from CDN). The design language:

- **Background palette**: `#0a0e1a` page · `#121829` secondary · `#1a2035` cards
- **Accent gradient**: `#f97316 → #fb923c → #fbbf24` (orange/amber)
- **Text**: `#e8ecf4` primary · `#8892a8` secondary · `#5a6580` muted
- **Borders**: `#2a3555`
- Cards have `border-radius: 12px`, subtle box-shadow, and lift on hover
- Sections open with a fade-in slide-up animation (`opacity 0→1, translateY 20px→0`)
- **Chart containers must have explicit height** to prevent Chart.js collapse. Apply:
  ```css
  .chart-card { min-height: 360px; display: flex; flex-direction: column; overflow: hidden; }
  .chart-card canvas { display: block; width: 100% !important; height: 290px !important; }
  ```

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

**8. Key insights** — 2-column grid of insight cards (icon + title + quote from reviews). Each card must use a quote that is **unique across all displayed cards** — deduplicate by the first 60 characters of the quote text.

**9. Action items** — numbered list with priority pills (colored borders matching severity)

---

## Step 5: Final summary

Tell the user:
- Total reviews analyzed and the date range covered
- Overall sentiment split (e.g., "71% positive · 15% neutral · 14% negative")
- Top 3 complaint themes
- Top 3 action items

End with exactly this closing line (fill in the filename and resolve to absolute path):

> Your report **[productname_report_timestamp.html](absolute/path/to/file)** is ready.

---

## Scripts

### scripts/generate_html.py

Generates the dark-theme HTML dashboard. Placed at `[OUTPUT_DIR]/scripts/generate_html.py`. Run as:

```bash
python [OUTPUT_DIR]/scripts/generate_html.py \
  --data [OUTPUT_DIR]/analysis_results.json \
  --output [OUTPUT_DIR]/[productname]_report_[timestamp].html
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

> **Implementation note:** The generator embeds HTML/CSS/JS inside a Python string. Because CSS and JS make heavy use of `{` and `}`, **do not use Python f-strings** for the template body — they require escaping every brace as `{{`/`}}`, which is error-prone at scale. Instead, write the HTML as a plain string with `__PLACEHOLDER__` tokens and replace them with `.replace()`, or use `string.Template` with `$var` syntax which has no conflict with CSS/JS braces.
