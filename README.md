# Customer Review Analyst

**[🌐 Product Page](https://adrianwwwang.github.io/customer-review-analyst/)**

An [agent skill](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) that fetches, analyzes, and visualizes customer reviews into a polished, interactive report — in one conversation.

Works with **Claude Code**, **GitHub Copilot**, **Cursor**, **Codex**, **Kiro**, **OpenClaw**, and any tool that supports the open `SKILL.md` standard.

Give it a product review URL or just a product name, and it automatically produces two files in your current folder — no further questions asked.

---

## What it does

| Output | Description |
|--------|-------------|
| **HTML dashboard** | Dark-theme interactive single-file report with trend charts, sentiment analysis, complaint themes, verbatim quotes, and action items |
| **PowerPoint slides** | 7-slide deck ready for stakeholder presentations |

**Example output** — TikTok analysis · 154 reviews · Dec 2025–Mar 2026 · 2.18 avg rating · 67.5% negative sentiment:

![TikTok Customer Review Analysis Dashboard](examples/tiktok_review_analysis.png)

---

## Architecture

The skill is a single `SKILL.md` manifest that orchestrates the AI through a 6-step workflow:

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
Step 3 ── Analyze (Python script written + run by the AI)
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
├── skills/
│   └── customer-review-analyst/
│       ├── SKILL.md                    # Skill definition — orchestration instructions
│       └── scripts/
│           └── generate_html.py        # HTML dashboard generator (~750 lines, Chart.js)
├── cursor/
│   └── rules/
│       └── customer-review-analyst.mdc # Cursor rules file
├── github-copilot/
│   └── copilot-instructions.md         # Drop into .github/copilot-instructions.md
├── .claude-plugin/
│   ├── plugin.json                     # Claude Code marketplace metadata
│   └── marketplace.json               # Claude Code marketplace registry
└── evals/
    └── evals.json                      # Evaluation test cases
```

**Runtime dependencies** (the AI installs these on demand via `pip`):

| Package | Purpose | Required? |
|---------|---------|-----------|
| Chart.js | Interactive charts in HTML | Auto — loaded from CDN |
| `python-pptx` | PowerPoint generation | Only for `.pptx` output |
| `matplotlib` | Chart images in slides | Only for `.pptx` output |
| `weasyprint` | HTML → PDF | Only for `.pdf` output |

---

## Installation

### <img src="assets/claude-light.png" height="37" valign="middle"> Claude

```bash
# Clone the repo
git clone https://github.com/adrianwwwang/customer-review-analyst.git

# Copy the skill to your Claude skills directory
cp -r customer-review-analyst/skills/customer-review-analyst ~/.claude/skills/
```

Restart Claude Code — the skill is auto-detected and available in all projects.

**Uninstall:**
```bash
rm -rf ~/.claude/skills/customer-review-analyst
```

---

### <img src="assets/github-copilot-icon.png" height="37" valign="middle"> GitHub Copilot

#### <img src="assets/vscode.png" height="20" valign="middle"> VS Code

**Global skill (available across all projects):**
```bash
mkdir -p ~/.copilot/skills/customer-review-analyst
curl -o ~/.copilot/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Project skill (current repo only):**
```bash
mkdir -p .github/skills/customer-review-analyst
curl -o .github/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Uninstall:**
```bash
# Global
rm -rf ~/.copilot/skills/customer-review-analyst
# Project
rm -rf .github/skills/customer-review-analyst
```

#### <img src="assets/jetbrains.png" height="20" valign="middle"> JetBrains

**Global skill (available across all projects):**
```bash
mkdir -p ~/.config/github-copilot/intellij/skills/customer-review-analyst
curl -o ~/.config/github-copilot/intellij/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Project skill (current repo only):**
```bash
mkdir -p .github/skills/customer-review-analyst
curl -o .github/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Uninstall:**
```bash
# Global
rm -rf ~/.config/github-copilot/intellij/skills/customer-review-analyst
# Project
rm -rf .github/skills/customer-review-analyst
```

---

### <img src="assets/cursor.png" height="37" valign="middle"> Cursor

**Global skill (available across all projects):**
```bash
mkdir -p ~/.cursor/skills/customer-review-analyst
curl -o ~/.cursor/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Project skill (current repo only):**
```bash
mkdir -p .cursor/skills/customer-review-analyst
curl -o .cursor/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

Cursor auto-detects the skill from context, or invoke it manually with `/` in chat.

**Uninstall:**
```bash
# Global
rm -rf ~/.cursor/skills/customer-review-analyst
# Project
rm -rf .cursor/skills/customer-review-analyst
```

---

### <img src="assets/codex-light.png" height="37" valign="middle"> Codex

**Global install (all projects):**
```bash
mkdir -p ~/.codex/skills/customer-review-analyst
curl -o ~/.codex/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Project-level install:**
```bash
mkdir -p .agents/skills/customer-review-analyst
curl -o .agents/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Uninstall:**
```bash
# Global
rm -rf ~/.codex/skills/customer-review-analyst
# Project
rm -rf .agents/skills/customer-review-analyst
```

---

### <img src="assets/kiro.svg" height="37" valign="middle"> Kiro

**Option A — Steering file (always-on, recommended):**
```bash
mkdir -p .kiro/steering
curl -o .kiro/steering/customer-review-analyst.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Option B — Agent Skill (context-triggered):**
```bash
mkdir -p .kiro/skills/customer-review-analyst
curl -o .kiro/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Uninstall:**
```bash
# Steering file
rm -f .kiro/steering/customer-review-analyst.md
# Agent skill
rm -rf .kiro/skills/customer-review-analyst
```

---

### <img src="assets/openclaw.png" height="37" valign="middle"> OpenClaw

**Global install (all projects):**
```bash
mkdir -p ~/.openclaw/skills/customer-review-analyst
curl -o ~/.openclaw/skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Project-level install:**
```bash
mkdir -p skills/customer-review-analyst
curl -o skills/customer-review-analyst/SKILL.md \
  https://raw.githubusercontent.com/adrianwwwang/customer-review-analyst/main/skills/customer-review-analyst/SKILL.md
```

**Uninstall:**
```bash
# Global
rm -rf ~/.openclaw/skills/customer-review-analyst
# Project
rm -rf skills/customer-review-analyst
```

---

## How to

Open Claude Code (or any supported AI editor) and type:

```
/customer-review-analyst https://www.trustpilot.com/review/tiktok.com
```

That's it. The skill fetches the last 6 months of reviews, analyzes them, and drops two files in your current folder — no further questions asked:

```
./customer_review_report_[product]_[date].html    ← interactive dashboard
./customer_review_slides_[product]_[date].pptx    ← ready-to-present slides
```

If you don't include a URL, the skill shows a single prompt asking for one, then proceeds automatically.

---

## Usage

Once installed, trigger the skill with a URL:

```
/customer-review-analyst https://www.trustpilot.com/review/tiktok.com
```

Or with a product name (the skill finds the review page for you):

```
/customer-review-analyst Bose QuietComfort 45
```

**Fixed defaults — no questions asked:**

| Setting | Value |
|---------|-------|
| Time range | Last 6 months |
| Output | HTML dashboard + PowerPoint slides |
| Review data | Fetch fresh, never saved to disk |
| Output directory | Current working directory |

### Output file structure

```
./
├── customer_review_report_[product]_[date].html    ← always generated
├── customer_review_slides_[product]_[date].pptx    ← always generated
└── scripts/
    ├── generate_html.py
    ├── analyze_reviews.py
    └── generate_slides.py
```

---

## Supported review sources

Works best with:
- **Trustpilot** — `trustpilot.com/review/[company-slug]`
- **Amazon** — product pages with `#customerReviews` anchor
- **Google Play Store** — may fall back to Trustpilot for JS-heavy pages
- **Apple App Store** — via direct app page URL

If a site blocks scraping, the AI will suggest alternative platforms for the same product.

---

## Contributing

Pull requests welcome. For major changes, please open an issue first.

---

## License

MIT © [adrianwwwang](https://github.com/adrianwwwang)
