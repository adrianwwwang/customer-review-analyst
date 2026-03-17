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

## Step 1: Gather inputs before doing anything

Ask the user these **five questions up front** and wait for all answers before proceeding:

**1. Data source**
> "Please share a product review page URL (e.g. an Amazon, Trustpilot, Google Reviews, or
> app store page). If you only have a product name, I can search for one — just let me know."

A direct URL is recommended because product name searches may land on the wrong product.

**2. Time range**
> "I'll analyze the last **6 months** of reviews by default. Would you like to adjust this?
> (e.g., 3 months, 1 year, all available reviews)"

**3. Output formats** — present as a checklist:
- ☑ **HTML interactive dashboard** (always generated)
- ☐ **Slides deck** (.pptx) — optional
- ☐ **PDF report** — optional

**4. Review data**
> "For the review data, would you like to:
> - **(A) Load from an existing JSON file** I've saved before? (provide the file path)
> - **(B) Fetch fresh data and save it** as a new JSON file for future reuse
> - **(C) Fetch fresh data but don't save it**"

**5. Output destination**
> "Where should I save the report files?
> - **Default:** current working directory (press Enter / say 'default')
> - **Custom:** provide an absolute or relative path (e.g. `~/Desktop/reports/my-product`)"

If the user provides a path that does not exist, create it with `mkdir -p` before writing any files.
Store this value as `OUTPUT_DIR` and prefix **all** output file paths with it throughout Steps 2–5.

---

## Step 2: Get the review data

### If loading from existing JSON (option A)
Read the file the user provided. Validate it contains reviews with at least `date`, `rating`,
and `text` fields. Skip to Step 3.

### If fetching from a URL (options B or C)
Use `WebFetch` to retrieve the review page. For each review, extract:
- `date` (ISO format: YYYY-MM-DD)
- `rating` (number 1–5)
- `text` (full review body)
- `title` (if present)
- `verified` (boolean, if present)
- `helpful_votes` (integer, if present)

Filter to reviews within the requested time range. If the page paginates, follow pagination
links — aim for at least 50 reviews for meaningful analysis. If you get fewer, note it.

**If a site blocks scraping:** Inform the user and suggest trying a different platform URL
for the same product (e.g., Amazon instead of the brand's own site).

**If saving data (option B):** After fetching, write raw reviews to:
`[OUTPUT_DIR]/reviews_[product-slug]_[YYYY-MM-DD].json`

### If product name only (no URL)
Use `WebSearch` to find the most prominent review page. Show the user the URL you found and
ask them to confirm before fetching.

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

## Step 5: Generate optional outputs

### Slides deck (.pptx) — if requested
Use `python-pptx` to create a PowerPoint. For charts, save Plotly figures as PNG images
first (using `kaleido` or `orca`), then embed them. Slides:
1. Title: product name, analysis period, total reviews
2. Key metrics: avg rating, sentiment breakdown pie
3. Rating trend chart
4. Sentiment trend chart
5. Rating segmentation chart
6. Top complaints (combine onto 1–2 slides with quotes)
7. Action items

Save as: `[OUTPUT_DIR]/customer_review_slides_[product-slug]_[YYYY-MM-DD].pptx`

### PDF report — if requested
Convert the HTML to PDF. Try in order:
```bash
weasyprint [OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].html \
           [OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].pdf
# or
python -m pdfkit [OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].html \
                 [OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].pdf
```
Note to user that interactive chart features won't carry over to PDF — that's expected.

Save as: `[OUTPUT_DIR]/customer_review_report_[product-slug]_[YYYY-MM-DD].pdf`

---

## Step 6: Final summary

Tell the user:
- **Output directory** used (`OUTPUT_DIR`, resolved to absolute path)
- File paths for all generated outputs
- Total reviews analyzed and the date range covered
- Overall sentiment split (e.g., "71% positive · 15% neutral · 14% negative")
- Top 3 complaint themes
- Top 3 action items

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
