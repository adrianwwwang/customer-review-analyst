# Customer Review Analyst

A [Claude Code](https://claude.ai/code) skill that fetches, analyzes, and visualizes customer reviews into a polished, interactive report — in one conversation.

Give it a product review URL or just a product name, and it produces a self-contained HTML dashboard with trend charts, sentiment analysis, top complaint themes, verbatim quotes, and prioritized action items. Optionally generates PowerPoint slides and a PDF report too.

---

## What it does

| Output | Description | Always? |
|--------|-------------|---------|
| **HTML dashboard** | Dark-theme interactive single-file report | Yes |
| **PowerPoint slides** | 7-slide deck for stakeholder presentations | Optional |
| **PDF report** | Static version of the dashboard | Optional |
| **Raw JSON** | Saved review data for future reuse | Optional |

**Example:** [TikTok analysis](examples/tiktok/) — 154 reviews · Dec 2025–Mar 2026 · 2.18 avg rating · 67.5% negative sentiment

---

## Architecture

The skill is a single `SKILL.md` manifest that orchestrates Claude through a 6-step workflow:

```
User request
    │
    ▼
Step 1 ── Gather inputs
          URL or product name · time range · output formats · output directory
    │
    ▼
Step 2 ── Get review data
          WebFetch from URL  ──or──  WebSearch for product  ──or──  Load existing JSON
          Paginate to collect 50+ reviews · filter by time range · optionally save raw JSON
    │
    ▼
Step 3 ── Analyze (Python script written + run by Claude)
          ├── Sentiment classification  (star rating + text override)
          ├── Monthly aggregation       (avg rating, counts, sentiment %)
          ├── Complaint theme extraction (5–7 themes, 2–3 verbatim quotes each)
          └── Action item generation    (1 per theme, priority ranked)
    │
    ▼
Step 4 ── Generate HTML dashboard
          scripts/generate_html.py · Chart.js · dark theme · fully self-contained
    │
    ▼
Step 5 ── Optional outputs
          python-pptx → .pptx slides   │   weasyprint/pdfkit → .pdf
    │
    ▼
Step 6 ── Summary
          File paths · sentiment split · top 3 complaints · top 3 actions
```

**Key files:**

```
customer-review-analyst/
├── SKILL.md                    # Skill definition — the orchestration instructions for Claude
├── scripts/
│   └── generate_html.py        # HTML dashboard generator (~750 lines, Chart.js, dark theme)
├── evals/
│   └── evals.json              # Evaluation test cases
└── examples/
    └── tiktok/
        ├── analysis_results.json   # Sample structured analysis output
        └── reviews_sample.json     # Sample raw review data (154 reviews, names anonymized)
```

**Runtime dependencies** (Claude installs these on demand via `pip`):

| Package | Purpose | Required? |
|---------|---------|-----------|
| Chart.js | Interactive charts in HTML | Auto — loaded from CDN |
| `python-pptx` | PowerPoint generation | Only for `.pptx` output |
| `matplotlib` | Chart images in slides | Only for `.pptx` output |
| `weasyprint` | HTML → PDF | Only for `.pdf` output |
| `pdfkit` | Alternative HTML → PDF | Only for `.pdf` output |

---

## Installation

### Option A — Claude Code skills directory (manual, recommended now)

1. Clone this repo:
   ```bash
   git clone https://github.com/adrianwwwang/customer-review-analyst.git
   ```

2. Copy the skill into Claude Code's skills directory:
   ```bash
   mkdir -p ~/.claude/skills/customer-review-analyst

   cp customer-review-analyst/SKILL.md ~/.claude/skills/customer-review-analyst/
   cp -r customer-review-analyst/scripts ~/.claude/skills/customer-review-analyst/
   ```

3. Restart Claude Code. The skill will be auto-detected and available in all projects.

4. *(Optional)* Pre-install Python dependencies so Claude doesn't need to install them at runtime:
   ```bash
   pip install python-pptx matplotlib    # for .pptx slides
   pip install weasyprint                # for .pdf report
   ```

### Option B — Claude Code marketplace

> **Note:** The Claude Code skills marketplace is actively evolving. Check the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for the latest installation commands as the ecosystem matures.

When CLI-based skill installation is available, it will likely look like:

```bash
claude skill install github:adrianwwwang/customer-review-analyst
# or
claude plugin install adrianwwwang/customer-review-analyst
```

Watch this repo for updates as the official marketplace launches.

### Verify installation

Open a new Claude Code conversation and try:
```
Analyze customer reviews for https://www.trustpilot.com/review/notion.so
```

Claude should trigger the skill and ask for your inputs.

---

## Usage

Once installed, speak to Claude naturally. The skill triggers on phrases like:

- `"Analyze reviews for [product name or URL]"`
- `"What are customers saying about [product]?"`
- `"Give me a review dashboard for [URL]"`
- `"Summarize customer complaints for [product]"`
- `"Product feedback summary for [URL]"`
- `"Review analysis of [product]"`

### Example prompts

```
Analyze customer reviews at https://www.amazon.com/dp/B07S829LBX for the last 6 months.
HTML only is fine.
```

```
What are customers saying about Bose QuietComfort 45 headphones?
Save the data and also generate slides.
```

```
Load my existing review data at ~/data/reviews.json and generate a full report
with HTML, slides, and PDF for the last 3 months.
```

### What Claude will ask you

Before starting, Claude gathers **5 inputs** up front:

| # | Question | Default |
|---|----------|---------|
| 1 | Data source — URL, product name, or path to existing JSON | — |
| 2 | Time range | Last 6 months |
| 3 | Output formats — HTML (always), PPTX, PDF | HTML only |
| 4 | Review data — fetch & save / fetch only / load existing | Fetch only |
| 5 | Output directory | Current working directory |

### Output file structure

```
[output-dir]/
├── customer_review_report_[product]_[date].html    ← always
├── customer_review_slides_[product]_[date].pptx    ← if requested
├── customer_review_report_[product]_[date].pdf     ← if requested
├── reviews_[product]_[date].json                   ← if "save data" chosen
├── analysis_results.json                           ← intermediate analysis data
└── scripts/
    ├── generate_html.py
    ├── analyze_reviews.py
    └── generate_slides.py                          ← if PPTX requested
```

---

## Supported review sources

The skill uses `WebFetch` to scrape reviews. Works best with:

- **Trustpilot** — `trustpilot.com/review/[company-slug]`
- **Amazon** — product pages with `#customerReviews` anchor
- **Google Play Store** — may fall back to Trustpilot for JS-heavy pages
- **Apple App Store** — via direct app page URL

If a site blocks scraping, Claude will suggest alternative platforms for the same product.

You can also **load previously saved review data** from a JSON file — useful for re-running analysis with different time filters or output formats without re-fetching.

---

## Dashboard design

The HTML output is a polished dark-theme single-page dashboard:

- **Header** — gradient title, source URL, period badge, top-line stats
- **Sticky filter bar** — month dropdown that filters all charts simultaneously
- **KPI cards** — avg rating · negative % · neutral % · positive % · top complaint
- **Executive summary** — 1–2 sentence synthesis of key numbers
- **4 trend charts** — avg rating line · review volume bar · rating segmentation stacked bar · sentiment trend lines
- **Monthly data table** — sortable with sentiment bars and rating breakdown
- **Deep analysis** — sentiment donut · rating distribution donut · complaints bar chart
- **Key insights** — icon cards with representative quotes
- **Action items** — numbered list with High / Medium / Low priority pills

Color palette: `#0a0e1a` background · `#f97316→#fbbf24` orange/amber accents · Chart.js for all charts.

---

## Contributing

Pull requests welcome. For major changes, please open an issue first to discuss what you'd like to change.

### Running evals

The `evals/evals.json` file contains test cases for validating the skill output. Run them using the [Claude Code evals framework](https://docs.anthropic.com/en/docs/claude-code/evals).

---

## License

MIT © [adrianwwwang](https://github.com/adrianwwwang)
