"""
Generate a polished dark-theme customer review dashboard.

Design reference: jetbrainsAI.html
- Dark background palette: #0a0e1a / #121829 / #1a2035
- Orange/amber accent gradient: #f97316 → #fb923c → #fbbf24
- Chart.js for charts (not Plotly)
- Sticky filter bar, KPI cards, section titles with gradient icons,
  sortable data table, insights grid, complaints horizontal bar

Usage:
    python generate_html.py --data analysis_results.json --output report.html
"""

import json
import argparse
import os
from datetime import date


def generate(data: dict, output_path: str):
    product_name   = data.get("product_name", "Product")
    source_url     = data.get("source_url", "#")
    analysis_date  = data.get("analysis_date", str(date.today()))
    time_range     = data.get("time_range", {})
    total_reviews  = data.get("total_reviews", 0)
    overall_avg    = data.get("overall_avg_rating", 0)
    sentiment      = data.get("sentiment_breakdown", {})
    monthly_data   = data.get("monthly_data", [])
    complaint_themes = data.get("complaint_themes", [])
    action_items   = data.get("action_items", [])

    period_str = ""
    if time_range:
        period_str = f"{time_range.get('start','')} – {time_range.get('end','')}"

    pos_pct  = round(sentiment.get("positive", 0) * 100)
    neu_pct  = round(sentiment.get("neutral",  0) * 100)
    neg_pct  = round(sentiment.get("negative", 0) * 100)

    # ── JS data arrays ───────────────────────────────────────────────────────
    months_js    = json.dumps([d["month"] for d in monthly_data])
    avg_r_js     = json.dumps([d["avg_rating"] for d in monthly_data])
    cnt_js       = json.dumps([d["review_count"] for d in monthly_data])
    pos_pct_js   = json.dumps([d["sentiment_pct"].get("positive", 0) for d in monthly_data])
    neu_pct_js   = json.dumps([d["sentiment_pct"].get("neutral",  0) for d in monthly_data])
    neg_pct_js   = json.dumps([d["sentiment_pct"].get("negative", 0) for d in monthly_data])
    cnt1_js = json.dumps([d["rating_counts"].get("1", 0) for d in monthly_data])
    cnt2_js = json.dumps([d["rating_counts"].get("2", 0) for d in monthly_data])
    cnt3_js = json.dumps([d["rating_counts"].get("3", 0) for d in monthly_data])
    cnt4_js = json.dumps([d["rating_counts"].get("4", 0) for d in monthly_data])
    cnt5_js = json.dumps([d["rating_counts"].get("5", 0) for d in monthly_data])

    # Complaint chart data
    complaint_labels = json.dumps([t["theme"] for t in complaint_themes])
    complaint_counts = json.dumps([t["count"]  for t in complaint_themes])

    # ── Key Insights from complaint themes + sentiment ───────────────────────
    top_complaint = complaint_themes[0]["theme"] if complaint_themes else "N/A"
    trend_text = "stable" if len(monthly_data) < 2 else (
        "improving" if monthly_data[-1]["avg_rating"] > monthly_data[0]["avg_rating"] else "declining"
    )

    # Build insights HTML
    insight_defs = []
    severity_icon_bg = {"High": ("rgba(239,68,68,0.15)", "#f87171", "⚠"),
                        "Medium": ("rgba(245,158,11,0.15)", "#fbbf24", "💡"),
                        "Low": ("rgba(34,197,94,0.15)", "#4ade80", "✓")}
    for t in complaint_themes[:6]:
        ibg, icol, ico = severity_icon_bg.get(t["severity"], ("rgba(99,102,241,0.15)","#818cf8","📌"))
        quote = t["quotes"][0][:160] + ("…" if len(t["quotes"][0]) > 160 else "") if t["quotes"] else ""
        insight_defs.append((ibg, icol, ico, t["theme"], f"{t['count']} mentions", quote))

    insights_html = ""
    for ibg, icol, ico, title, sub, quote in insight_defs:
        insights_html += f"""
    <div class="insight-item fade-in">
      <div class="insight-icon" style="background:{ibg};color:{icol};">{ico}</div>
      <div class="insight-text">
        <h4>{title} <span class="insight-sub">({sub})</span></h4>
        <p>{quote}</p>
      </div>
    </div>"""

    # Action items HTML
    priority_colors = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
    actions_html = ""
    for i, a in enumerate(action_items, 1):
        pc = priority_colors.get(a.get("priority","Medium"), "#f59e0b")
        actions_html += f"""
    <div class="action-item fade-in">
      <div class="action-num">{i:02d}</div>
      <div class="action-body">
        <div class="action-header">
          <span class="priority-pill" style="background:{pc}22;color:{pc};border:1px solid {pc}55;">{a.get('priority','')}</span>
          <span class="action-theme">↳ {a.get('addresses_theme','')}</span>
        </div>
        <p class="action-text">{a.get('recommendation','')}</p>
      </div>
    </div>"""

    # Monthly data table rows
    table_rows = ""
    for d in monthly_data:
        avg = d["avg_rating"]
        stars = "★" * round(avg) + "☆" * (5 - round(avg))
        rat_cls = "rating-high" if avg >= 4 else ("rating-mid" if avg >= 2.5 else "rating-low")
        total = d["review_count"]
        pp = d["sentiment_pct"].get("positive", 0)
        np_ = d["sentiment_pct"].get("negative", 0)
        neu = d["sentiment_pct"].get("neutral", 0)
        table_rows += f"""
      <tr>
        <td>{d['month']}</td>
        <td>{total}</td>
        <td><span class="rating-badge {rat_cls}">{avg}</span></td>
        <td><span class="stars">{stars}</span></td>
        <td>
          <div class="sentiment-mini">
            <span style="color:#22c55e;font-size:11px">{pp:.0f}% pos</span>
            <span style="color:#6b7280;font-size:11px;margin:0 4px">·</span>
            <span style="color:#ef4444;font-size:11px">{np_:.0f}% neg</span>
          </div>
          <div class="sentiment-bar">
            <div class="sentiment-pos" style="width:{pp}%"></div>
            <div class="sentiment-mix" style="width:{neu}%"></div>
            <div class="sentiment-neg" style="width:{np_}%"></div>
          </div>
        </td>
        <td>
          {" ".join(f'<span class="topic-tag">{k}: {v}</span>' for k,v in list(d["rating_counts"].items())[:3])}
        </td>
      </tr>"""

    # Star display for header
    full_stars  = int(overall_avg)
    empty_stars = 5 - full_stars
    star_html   = "★" * full_stars + "☆" * empty_stars

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{product_name} — Review Analysis Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg-primary:    #0a0e1a;
  --bg-secondary:  #121829;
  --bg-card:       #1a2035;
  --bg-card-hover: #1f2845;
  --border-color:  #2a3555;
  --text-primary:  #e8ecf4;
  --text-secondary:#8892a8;
  --text-muted:    #5a6580;
  --accent-1:      #f97316;
  --accent-2:      #fb923c;
  --accent-3:      #fdba74;
  --accent-gradient: linear-gradient(135deg, #f97316 0%, #fb923c 50%, #fbbf24 100%);
  --success:  #22c55e;
  --warning:  #f59e0b;
  --danger:   #ef4444;
  --info:     #3b82f6;
  --shadow-md: 0 4px 12px rgba(0,0,0,.4);
  --shadow-lg: 0 8px 30px rgba(0,0,0,.5);
  --radius:    12px;
  --radius-sm: 8px;
}}
*{{ margin:0; padding:0; box-sizing:border-box; }}
body{{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:var(--bg-primary); color:var(--text-primary); line-height:1.6; overflow-x:hidden; }}
::-webkit-scrollbar{{ width:8px; }}
::-webkit-scrollbar-track{{ background:var(--bg-primary); }}
::-webkit-scrollbar-thumb{{ background:var(--border-color); border-radius:4px; }}
::-webkit-scrollbar-thumb:hover{{ background:var(--accent-1); }}

/* ── Header ────────────────────────────────────────────────────── */
.header{{
  background:linear-gradient(135deg,#0f1628 0%,#1a1a0a 50%,#0f1628 100%);
  border-bottom:1px solid var(--border-color);
  padding:40px 0 30px;
  position:relative; overflow:hidden;
}}
.header::before{{
  content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
  background:
    radial-gradient(ellipse at 30% 50%,rgba(249,115,22,.08) 0%,transparent 60%),
    radial-gradient(ellipse at 70% 50%,rgba(251,146,60,.06) 0%,transparent 60%);
  pointer-events:none;
}}
.header-content{{ max-width:1400px; margin:0 auto; padding:0 30px; position:relative; z-index:1; }}
.header-top{{ display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:20px; }}
.header-title h1{{
  font-size:28px; font-weight:700;
  background:var(--accent-gradient);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  margin-bottom:6px;
}}
.header-title .subtitle{{ font-size:14px; color:var(--text-secondary); display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
.header-title .subtitle a{{ color:var(--text-secondary); text-decoration:none; }}
.header-title .subtitle a:hover{{ color:var(--accent-3); }}
.badge{{ background:rgba(249,115,22,.15); color:var(--accent-3); padding:2px 10px; border-radius:20px; font-size:12px; font-weight:500; }}
.header-stats{{ display:flex; gap:30px; flex-wrap:wrap; }}
.header-stat{{ text-align:center; }}
.header-stat .stat-value{{ font-size:24px; font-weight:700; }}
.header-stat .stat-label{{ font-size:12px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:1px; }}

/* ── Filter bar ────────────────────────────────────────────────── */
.filter-bar{{
  position:sticky; top:0; z-index:100;
  background:rgba(18,24,41,.95); backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border-color); padding:12px 0;
}}
.filter-bar-content{{ max-width:1400px; margin:0 auto; padding:0 30px; display:flex; align-items:center; gap:16px; flex-wrap:wrap; }}
.filter-label{{ font-size:13px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.5px; }}
.filter-select{{ background:var(--bg-card); color:var(--text-primary); border:1px solid var(--border-color); padding:8px 16px; border-radius:var(--radius-sm); font-size:13px; cursor:pointer; }}
.filter-select:hover{{ border-color:var(--accent-1); }}
.filter-btn{{ background:var(--bg-card); color:var(--text-primary); border:1px solid var(--border-color); padding:8px 16px; border-radius:var(--radius-sm); font-size:13px; cursor:pointer; transition:all .2s; }}
.filter-btn:hover,.filter-btn.active{{ background:var(--accent-1); border-color:var(--accent-1); color:white; }}

/* ── Main ──────────────────────────────────────────────────────── */
.main{{ max-width:1400px; margin:0 auto; padding:30px; }}

.section-title{{
  font-size:20px; font-weight:700; color:var(--text-primary);
  margin-bottom:20px; padding-bottom:10px;
  border-bottom:2px solid var(--border-color);
  display:flex; align-items:center; gap:10px;
}}
.section-title .icon{{
  width:32px; height:32px;
  background:var(--accent-gradient);
  border-radius:var(--radius-sm);
  display:flex; align-items:center; justify-content:center; font-size:16px;
}}

/* ── KPI ───────────────────────────────────────────────────────── */
.kpi-row{{ display:grid; grid-template-columns:repeat(5,1fr); gap:16px; margin-bottom:30px; }}
@media(max-width:1024px){{ .kpi-row{{ grid-template-columns:repeat(3,1fr); }} }}
@media(max-width:640px){{ .kpi-row{{ grid-template-columns:repeat(2,1fr); }} }}
.kpi-card{{
  background:var(--bg-card); border:1px solid var(--border-color);
  border-radius:var(--radius); padding:20px; text-align:center;
  position:relative; overflow:hidden;
}}
.kpi-card::before{{ content:''; position:absolute; top:0; left:0; right:0; height:3px; }}
.kpi-card:nth-child(1)::before{{ background:var(--accent-1); }}
.kpi-card:nth-child(2)::before{{ background:var(--danger); }}
.kpi-card:nth-child(3)::before{{ background:var(--warning); }}
.kpi-card:nth-child(4)::before{{ background:var(--success); }}
.kpi-card:nth-child(5)::before{{ background:var(--info); }}
.kpi-value{{ font-size:28px; font-weight:800; margin-bottom:4px; }}
.kpi-label{{ font-size:12px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.5px; }}
.kpi-sub{{ font-size:11px; color:var(--text-muted); margin-top:4px; }}

/* ── Cards & Charts ───────────────────────────────────────────── */
.grid-2{{ display:grid; grid-template-columns:repeat(2,1fr); gap:24px; margin-bottom:30px; }}
.grid-3{{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-bottom:30px; }}
@media(max-width:1024px){{ .grid-2,.grid-3{{ grid-template-columns:1fr; }} }}
.card{{
  background:var(--bg-card); border:1px solid var(--border-color);
  border-radius:var(--radius); padding:24px;
  box-shadow:var(--shadow-md); transition:transform .2s,box-shadow .2s;
}}
.card:hover{{ transform:translateY(-2px); box-shadow:var(--shadow-lg); }}
.card-title{{ font-size:14px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.5px; margin-bottom:16px; }}
.card-full{{ grid-column:1/-1; }}
.chart-container{{ position:relative; width:100%; height:300px; }}
.chart-container-sm{{ position:relative; width:100%; height:260px; }}
.chart-container-donut{{ position:relative; width:100%; max-width:300px; margin:0 auto; height:280px; }}

/* ── Table ─────────────────────────────────────────────────────── */
.table-wrapper{{ overflow-x:auto; border-radius:var(--radius); border:1px solid var(--border-color); }}
table{{ width:100%; border-collapse:collapse; font-size:13px; }}
thead th{{
  background:var(--bg-secondary); color:var(--text-secondary);
  font-weight:600; text-transform:uppercase; letter-spacing:.5px; font-size:11px;
  padding:12px 16px; text-align:left; border-bottom:2px solid var(--border-color);
  cursor:pointer; user-select:none; white-space:nowrap;
}}
thead th:hover{{ color:var(--accent-3); }}
tbody tr{{ border-bottom:1px solid var(--border-color); transition:background .15s; }}
tbody tr:hover{{ background:rgba(249,115,22,.05); }}
tbody td{{ padding:12px 16px; color:var(--text-primary); vertical-align:middle; }}
.stars{{ color:var(--warning); font-size:13px; letter-spacing:1px; }}
.rating-badge{{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }}
.rating-low{{ background:rgba(239,68,68,.15); color:#f87171; }}
.rating-mid{{ background:rgba(245,158,11,.15); color:#fbbf24; }}
.rating-high{{ background:rgba(34,197,94,.15); color:#4ade80; }}
.topic-tag{{ display:inline-block; background:rgba(249,115,22,.1); color:var(--accent-3); padding:2px 8px; border-radius:4px; font-size:11px; margin:2px; white-space:nowrap; }}
.sentiment-bar{{ display:flex; height:5px; border-radius:3px; overflow:hidden; margin-top:4px; }}
.sentiment-neg{{ background:var(--danger); }}
.sentiment-mix{{ background:var(--warning); }}
.sentiment-pos{{ background:var(--success); }}
.sentiment-mini{{ display:flex; align-items:center; margin-bottom:2px; }}

/* ── Insights ──────────────────────────────────────────────────── */
.insights-grid{{ display:grid; grid-template-columns:repeat(2,1fr); gap:16px; margin-bottom:30px; }}
@media(max-width:768px){{ .insights-grid{{ grid-template-columns:1fr; }} }}
.insight-item{{
  background:var(--bg-card); border:1px solid var(--border-color);
  border-radius:var(--radius); padding:20px;
  display:flex; gap:16px; align-items:flex-start;
}}
.insight-icon{{ width:40px; height:40px; border-radius:var(--radius-sm); display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }}
.insight-text h4{{ font-size:14px; font-weight:600; margin-bottom:4px; }}
.insight-sub{{ font-size:12px; font-weight:400; color:var(--text-muted); }}
.insight-text p{{ font-size:13px; color:var(--text-secondary); line-height:1.5; font-style:italic; }}

/* ── Action items ──────────────────────────────────────────────── */
.actions-list{{ display:flex; flex-direction:column; gap:12px; margin-bottom:30px; }}
.action-item{{
  background:var(--bg-card); border:1px solid var(--border-color);
  border-radius:var(--radius); padding:18px 20px;
  display:flex; gap:16px; align-items:flex-start;
}}
.action-num{{ font-size:24px; font-weight:800; color:var(--text-muted); min-width:36px; padding-top:2px; }}
.action-body{{ flex:1; }}
.action-header{{ display:flex; align-items:center; gap:10px; margin-bottom:6px; flex-wrap:wrap; }}
.priority-pill{{ padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }}
.action-theme{{ font-size:12px; color:var(--text-muted); }}
.action-text{{ font-size:14px; color:var(--text-primary); line-height:1.6; }}

/* ── Executive summary ─────────────────────────────────────────── */
.exec-summary{{
  background:var(--bg-card);
  border:1px solid var(--border-color);
  border-left:4px solid var(--accent-1);
  border-radius:var(--radius);
  padding:20px 24px;
  margin-bottom:30px;
  font-size:14px;
  color:var(--text-secondary);
  line-height:1.8;
}}
.exec-summary strong{{ color:var(--text-primary); }}

/* ── Animations ────────────────────────────────────────────────── */
.fade-in{{ opacity:0; transform:translateY(20px); animation:fadeIn .5s ease forwards; }}
@keyframes fadeIn{{ to{{ opacity:1; transform:translateY(0); }} }}
.fade-in:nth-child(1){{ animation-delay:.05s; }}
.fade-in:nth-child(2){{ animation-delay:.10s; }}
.fade-in:nth-child(3){{ animation-delay:.15s; }}
.fade-in:nth-child(4){{ animation-delay:.20s; }}
.fade-in:nth-child(5){{ animation-delay:.25s; }}
.fade-in:nth-child(6){{ animation-delay:.30s; }}

/* ── How to ────────────────────────────────────────────────────── */
.howto-card{{
  background:linear-gradient(135deg,rgba(249,115,22,.08) 0%,rgba(251,146,60,.05) 100%);
  border:1px solid rgba(249,115,22,.25);
  border-radius:var(--radius); padding:28px 32px; margin-bottom:30px;
}}
.howto-desc{{ font-size:14px; color:var(--text-secondary); margin-bottom:20px; line-height:1.6; }}
.howto-steps{{ display:flex; flex-direction:column; gap:14px; }}
.howto-step{{ display:flex; align-items:flex-start; gap:16px; }}
.howto-num{{
  width:28px; height:28px; border-radius:50%; flex-shrink:0;
  background:var(--accent-gradient); color:#fff; font-size:13px; font-weight:700;
  display:flex; align-items:center; justify-content:center; margin-top:2px;
}}
.howto-text{{ font-size:14px; color:var(--text-primary); line-height:1.7; }}
.howto-text a{{ color:var(--accent-3); text-decoration:none; }}
.howto-text a:hover{{ text-decoration:underline; }}
.howto-code{{
  display:inline-block; margin-top:8px;
  background:var(--bg-secondary); border:1px solid var(--border-color);
  border-radius:var(--radius-sm); padding:10px 16px;
  font-family:'SF Mono','Fira Code','Consolas',monospace; font-size:13px;
  color:var(--accent-3); letter-spacing:.2px;
}}

/* ── Footer ────────────────────────────────────────────────────── */
.footer{{ text-align:center; padding:40px 30px; color:var(--text-muted); font-size:12px; border-top:1px solid var(--border-color); margin-top:40px; }}
</style>
</head>
<body>

<!-- Header -->
<header class="header">
  <div class="header-content">
    <div class="header-top">
      <div class="header-title">
        <h1>{product_name} — Review Analysis</h1>
        <div class="subtitle">
          <a href="{source_url}" target="_blank">🔗 {source_url[:60]}{"…" if len(source_url)>60 else ""}</a>
          <span class="badge">{period_str}</span>
          <span class="badge">Generated {analysis_date}</span>
        </div>
      </div>
      <div class="header-stats">
        <div class="header-stat">
          <div class="stat-value">{total_reviews:,}</div>
          <div class="stat-label">Reviews</div>
        </div>
        <div class="header-stat">
          <div class="stat-value" style="color:var(--warning);">{overall_avg} <span style="font-size:18px;">{star_html}</span></div>
          <div class="stat-label">Avg Rating</div>
        </div>
        <div class="header-stat">
          <div class="stat-value" style="color:var(--success);">{pos_pct}%</div>
          <div class="stat-label">Positive</div>
        </div>
      </div>
    </div>
  </div>
</header>

<!-- Sticky Filter Bar -->
<div class="filter-bar">
  <div class="filter-bar-content">
    <span class="filter-label">Filter:</span>
    <select class="filter-select" id="monthFilter" onchange="applyFilter()">
      <option value="all">All Months</option>
    </select>
    <button class="filter-btn active" onclick="resetFilter()">Reset</button>
  </div>
</div>

<!-- Main -->
<main class="main">

  <!-- KPI Row -->
  <div class="kpi-row">
    <div class="kpi-card fade-in">
      <div class="kpi-value" style="color:var(--accent-3);">{overall_avg}</div>
      <div class="kpi-label">Overall Avg Rating</div>
      <div class="kpi-sub">out of 5.0</div>
    </div>
    <div class="kpi-card fade-in">
      <div class="kpi-value" style="color:var(--danger);">{neg_pct}%</div>
      <div class="kpi-label">Negative Reviews</div>
      <div class="kpi-sub">1–2 stars</div>
    </div>
    <div class="kpi-card fade-in">
      <div class="kpi-value" style="color:var(--warning);">{neu_pct}%</div>
      <div class="kpi-label">Neutral Reviews</div>
      <div class="kpi-sub">3 stars</div>
    </div>
    <div class="kpi-card fade-in">
      <div class="kpi-value" style="color:var(--success);">{pos_pct}%</div>
      <div class="kpi-label">Positive Reviews</div>
      <div class="kpi-sub">4–5 stars</div>
    </div>
    <div class="kpi-card fade-in">
      <div class="kpi-value" style="color:var(--info);font-size:16px;">{complaint_themes[0]["theme"][:20] + "…" if complaint_themes and len(complaint_themes[0]["theme"])>20 else (complaint_themes[0]["theme"] if complaint_themes else "N/A")}</div>
      <div class="kpi-label">Top Complaint</div>
      <div class="kpi-sub">{complaint_themes[0]["count"] if complaint_themes else 0} mentions</div>
    </div>
  </div>

  <!-- Executive Summary -->
  <div class="exec-summary fade-in">
    <strong>Executive Summary:</strong> {product_name} received <strong>{total_reviews:,} reviews</strong> over the period {period_str},
    with an average rating of <strong>{overall_avg}/5</strong>.
    Sentiment is <strong>{pos_pct}% positive</strong>, {neu_pct}% neutral, and {neg_pct}% negative.
    The trend is <strong>{trend_text}</strong> over the analysis window.
    The top customer complaint is <strong>{top_complaint}</strong>
    {f"({complaint_themes[0]['count']} mentions, {complaint_themes[0]['severity']} severity)" if complaint_themes else ""}.
  </div>

  <!-- Monthly Trends -->
  <div class="section-title fade-in"><div class="icon">📈</div> Monthly Trends</div>
  <div class="grid-2 fade-in">
    <div class="card">
      <div class="card-title">Average Rating by Month</div>
      <div class="chart-container"><canvas id="avgRatingChart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">Review Volume by Month</div>
      <div class="chart-container"><canvas id="reviewCountChart"></canvas></div>
    </div>
  </div>
  <div class="grid-2 fade-in">
    <div class="card">
      <div class="card-title">Rating Distribution by Month (Stacked)</div>
      <div class="chart-container"><canvas id="ratingDistChart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">Sentiment Trend by Month</div>
      <div class="chart-container"><canvas id="sentimentTrendChart"></canvas></div>
    </div>
  </div>

  <!-- Monthly Data Table -->
  <div class="section-title fade-in"><div class="icon">📊</div> Monthly Data Table</div>
  <div class="card card-full fade-in" style="margin-bottom:30px;">
    <div class="table-wrapper">
      <table id="dataTable">
        <thead>
          <tr>
            <th onclick="sortTable(0)">Month ↕</th>
            <th onclick="sortTable(1)">Reviews ↕</th>
            <th onclick="sortTable(2)">Avg Rating ↕</th>
            <th>Stars</th>
            <th>Sentiment</th>
            <th>Rating Breakdown</th>
          </tr>
        </thead>
        <tbody id="dataTableBody">{table_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Deep Analysis -->
  <div class="section-title fade-in"><div class="icon">🔍</div> Deep Analysis</div>
  <div class="grid-3 fade-in">
    <div class="card">
      <div class="card-title">Sentiment Split</div>
      <div class="chart-container-donut"><canvas id="sentimentPie"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">Rating Distribution</div>
      <div class="chart-container-donut"><canvas id="ratingDonut"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">Top Complaint Categories</div>
      <div class="chart-container-sm"><canvas id="complaintsChart"></canvas></div>
    </div>
  </div>

  <!-- Key Insights -->
  <div class="section-title fade-in"><div class="icon">💡</div> Key Insights</div>
  <div class="insights-grid">
    {insights_html}
  </div>

  <!-- Action Items -->
  <div class="section-title fade-in"><div class="icon">✅</div> Recommended Actions</div>
  <div class="actions-list">
    {actions_html}
  </div>

  <!-- How to -->
  <div class="section-title fade-in" id="how-to"><div class="icon">🚀</div> How to Get This Report</div>
  <div class="howto-card fade-in">
    <p class="howto-desc">Generate an interactive report like this for any product — in one command.</p>
    <div class="howto-steps">
      <div class="howto-step">
        <div class="howto-num">1</div>
        <div class="howto-text">
          <strong>Install the skill</strong> (one-time setup):
          <div class="howto-code">cp -r customer-review-analyst/skills/customer-review-analyst ~/.claude/skills/</div>
          <a href="https://github.com/adrianwwwang/customer-review-analyst#installation" target="_blank" style="display:inline-block;margin-top:6px;font-size:13px;">Full installation guide (Claude, Copilot, Cursor…) →</a>
        </div>
      </div>
      <div class="howto-step">
        <div class="howto-num">2</div>
        <div class="howto-text"><strong>Open Claude Code chat</strong> in any project folder</div>
      </div>
      <div class="howto-step">
        <div class="howto-num">3</div>
        <div class="howto-text">
          <strong>Type the command with any review page URL:</strong>
          <div class="howto-code">/customer-review-analyst https://www.trustpilot.com/review/tiktok.com</div>
        </div>
      </div>
    </div>
    <p class="howto-desc" style="margin-top:20px;margin-bottom:0;">The full dashboard and slides are generated automatically — no other questions asked. &nbsp;<a href="https://github.com/adrianwwwang/customer-review-analyst#how-to" target="_blank">Learn more →</a></p>
  </div>

</main>

<footer class="footer">
  <p>{product_name} Review Analysis Dashboard · {period_str} · {total_reviews:,} reviews analyzed</p>
  <p style="margin-top:4px;">Generated {analysis_date} · Customer Review Analyst</p>
</footer>

<script>
// ── Data ─────────────────────────────────────────────────────────────────
const MONTHS    = {months_js};
const AVG_R     = {avg_r_js};
const CNT       = {cnt_js};
const POS_PCT   = {pos_pct_js};
const NEU_PCT   = {neu_pct_js};
const NEG_PCT   = {neg_pct_js};
const CNT1 = {cnt1_js}, CNT2 = {cnt2_js}, CNT3 = {cnt3_js}, CNT4 = {cnt4_js}, CNT5 = {cnt5_js};
const COMP_LABELS = {complaint_labels};
const COMP_COUNTS = {complaint_counts};
const OVERALL_AVG = {overall_avg};

// ── Chart.js global defaults ──────────────────────────────────────────────
Chart.defaults.color = '#8892a8';
Chart.defaults.borderColor = '#2a3555';

const COLORS = {{
  orange:  '#f97316',
  amber:   '#fb923c',
  yellow:  '#fbbf24',
  green:   '#22c55e',
  red:     '#ef4444',
  yellow2: '#f59e0b',
  blue:    '#3b82f6',
  purple:  '#8b5cf6',
  pink:    '#ec4899',
  teal:    '#14b8a6',
}};

// ── Filter state ──────────────────────────────────────────────────────────
let selectedMonth = 'all';

function buildMonthFilter() {{
  const sel = document.getElementById('monthFilter');
  MONTHS.forEach(m => {{
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    sel.appendChild(opt);
  }});
}}

function getFilteredIndices() {{
  if (selectedMonth === 'all') return MONTHS.map((_,i)=>i);
  const idx = MONTHS.indexOf(selectedMonth);
  return idx >= 0 ? [idx] : MONTHS.map((_,i)=>i);
}}

function applyFilter() {{
  selectedMonth = document.getElementById('monthFilter').value;
  updateCharts();
}}

function resetFilter() {{
  selectedMonth = 'all';
  document.getElementById('monthFilter').value = 'all';
  updateCharts();
}}

// ── Chart instances ───────────────────────────────────────────────────────
let charts = {{}};

function filteredData(arr) {{
  return getFilteredIndices().map(i => arr[i]);
}}
function filteredMonths() {{
  return getFilteredIndices().map(i => MONTHS[i]);
}}

function makeGradient(ctx, color) {{
  const g = ctx.createLinearGradient(0, 0, 0, 300);
  g.addColorStop(0, color + '44');
  g.addColorStop(1, color + '00');
  return g;
}}

function initCharts() {{
  const fm = filteredMonths();

  // 1. Avg Rating Line
  const ctx1 = document.getElementById('avgRatingChart').getContext('2d');
  charts.avgRating = new Chart(ctx1, {{
    type: 'line',
    data: {{
      labels: fm,
      datasets: [
        {{ label: 'Avg Rating', data: filteredData(AVG_R), borderColor: COLORS.orange,
           backgroundColor: makeGradient(ctx1, COLORS.orange), tension: 0.4, pointRadius: 4,
           pointBackgroundColor: COLORS.orange, fill: true }},
        {{ label: 'Overall avg', data: fm.map(()=>OVERALL_AVG), borderColor: '#5a6580',
           borderDash: [6,4], pointRadius: 0, fill: false }}
      ]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      scales: {{ y: {{ min:0, max:5, ticks: {{ stepSize:1 }} }}, x: {{ ticks: {{ maxRotation:45 }} }} }},
      plugins: {{ legend: {{ display:true }}, tooltip: {{ mode:'index' }} }}
    }}
  }});

  // 2. Review Count Bar
  const ctx2 = document.getElementById('reviewCountChart').getContext('2d');
  charts.reviewCount = new Chart(ctx2, {{
    type: 'bar',
    data: {{
      labels: fm,
      datasets: [{{ label: 'Reviews', data: filteredData(CNT),
        backgroundColor: COLORS.amber + 'aa', borderColor: COLORS.amber, borderWidth: 1,
        borderRadius: 4 }}]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins: {{ legend: {{ display:false }} }},
      scales: {{ x: {{ ticks: {{ maxRotation:45 }} }} }}
    }}
  }});

  // 3. Rating Distribution Stacked Bar
  charts.ratingDist = new Chart(document.getElementById('ratingDistChart'), {{
    type: 'bar',
    data: {{
      labels: fm,
      datasets: [
        {{ label: '★1', data: filteredData(CNT1), backgroundColor: '#ef4444cc', stack:'s' }},
        {{ label: '★2', data: filteredData(CNT2), backgroundColor: '#f97316cc', stack:'s' }},
        {{ label: '★3', data: filteredData(CNT3), backgroundColor: '#f59e0bcc', stack:'s' }},
        {{ label: '★4', data: filteredData(CNT4), backgroundColor: '#84cc16cc', stack:'s' }},
        {{ label: '★5', data: filteredData(CNT5), backgroundColor: '#22c55ecc', stack:'s' }},
      ]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      scales: {{ x: {{ stacked:true, ticks:{{ maxRotation:45 }} }}, y: {{ stacked:true }} }},
      plugins: {{ legend: {{ display:true }} }}
    }}
  }});

  // 4. Sentiment Trend Lines
  charts.sentimentTrend = new Chart(document.getElementById('sentimentTrendChart'), {{
    type: 'line',
    data: {{
      labels: fm,
      datasets: [
        {{ label: 'Positive %', data: filteredData(POS_PCT), borderColor: COLORS.green, tension:0.4, pointRadius:3, fill:false }},
        {{ label: 'Neutral %',  data: filteredData(NEU_PCT), borderColor: COLORS.yellow2, tension:0.4, pointRadius:3, fill:false }},
        {{ label: 'Negative %', data: filteredData(NEG_PCT), borderColor: COLORS.red, tension:0.4, pointRadius:3, fill:false }}
      ]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      scales: {{ y: {{ min:0, max:100, ticks:{{ callback: v => v+'%' }} }}, x:{{ ticks:{{ maxRotation:45 }} }} }},
      plugins: {{ legend:{{ display:true }}, tooltip:{{ callbacks:{{ label: ctx => ctx.dataset.label+': '+ctx.raw.toFixed(1)+'%' }} }} }}
    }}
  }});

  // 5. Sentiment Pie
  const totPos = POS_PCT.reduce((a,b)=>a+b,0)/POS_PCT.length;
  const totNeu = NEU_PCT.reduce((a,b)=>a+b,0)/NEU_PCT.length;
  const totNeg = NEG_PCT.reduce((a,b)=>a+b,0)/NEG_PCT.length;
  charts.sentimentPie = new Chart(document.getElementById('sentimentPie'), {{
    type: 'doughnut',
    data: {{
      labels: ['Positive','Neutral','Negative'],
      datasets: [{{ data:[totPos,totNeu,totNeg],
        backgroundColor:[COLORS.green+'cc',COLORS.yellow2+'cc',COLORS.red+'cc'],
        borderColor:['#1a2035'], borderWidth:2 }}]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ position:'bottom' }}, tooltip:{{ callbacks:{{ label: c => c.label+': '+c.raw.toFixed(1)+'%' }} }} }}
    }}
  }});

  // 6. Rating Donut
  const r1=CNT1.reduce((a,b)=>a+b,0), r2=CNT2.reduce((a,b)=>a+b,0),
        r3=CNT3.reduce((a,b)=>a+b,0), r4=CNT4.reduce((a,b)=>a+b,0),
        r5=CNT5.reduce((a,b)=>a+b,0);
  charts.ratingDonut = new Chart(document.getElementById('ratingDonut'), {{
    type: 'doughnut',
    data: {{
      labels: ['★1','★2','★3','★4','★5'],
      datasets: [{{ data:[r1,r2,r3,r4,r5],
        backgroundColor:['#ef4444cc','#f97316cc','#f59e0bcc','#84cc16cc','#22c55ecc'],
        borderColor:['#1a2035'], borderWidth:2 }}]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ position:'bottom' }} }}
    }}
  }});

  // 7. Complaints Horizontal Bar
  charts.complaints = new Chart(document.getElementById('complaintsChart'), {{
    type: 'bar',
    data: {{
      labels: COMP_LABELS,
      datasets: [{{ label: 'Mentions', data: COMP_COUNTS,
        backgroundColor: COLORS.orange + 'aa', borderColor: COLORS.orange,
        borderWidth:1, borderRadius:4 }}]
    }},
    options: {{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ display:false }} }},
      scales: {{ x: {{ beginAtZero:true }} }}
    }}
  }});
}}

function updateCharts() {{
  const fm = filteredMonths();
  const upd = (chart, ...datasets) => {{
    chart.data.labels = fm;
    datasets.forEach((d,i) => {{ chart.data.datasets[i].data = d; }});
    chart.update();
  }};
  upd(charts.avgRating, filteredData(AVG_R), fm.map(()=>OVERALL_AVG));
  upd(charts.reviewCount, filteredData(CNT));
  upd(charts.ratingDist, filteredData(CNT1), filteredData(CNT2), filteredData(CNT3), filteredData(CNT4), filteredData(CNT5));
  upd(charts.sentimentTrend, filteredData(POS_PCT), filteredData(NEU_PCT), filteredData(NEG_PCT));
}}

// ── Sort table ────────────────────────────────────────────────────────────
let sortDir = {{}};
function sortTable(col) {{
  const tbody = document.getElementById('dataTableBody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[col] = !sortDir[col];
  rows.sort((a,b) => {{
    const va = a.cells[col].textContent.trim();
    const vb = b.cells[col].textContent.trim();
    const na = parseFloat(va), nb = parseFloat(vb);
    const cmp = isNaN(na) ? va.localeCompare(vb) : na - nb;
    return sortDir[col] ? cmp : -cmp;
  }});
  rows.forEach(r => tbody.appendChild(r));
}}

// ── Init ──────────────────────────────────────────────────────────────────
buildMonthFilter();
initCharts();
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.data) as f:
        data = json.load(f)
    generate(data, args.output)
