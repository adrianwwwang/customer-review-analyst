#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def stars_from_rating(avg_rating: float) -> str:
    rounded = max(0, min(5, round(avg_rating)))
    return "★" * rounded + "☆" * (5 - rounded)


def priority_class(priority: str) -> str:
    p = (priority or "").lower()
    if p == "high":
        return "priority-high"
    if p == "medium":
        return "priority-medium"
    return "priority-low"


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_html(data: dict) -> str:
    product_name = data.get("product_name", "Product")
    source_url = data.get("source_url", "")
    analysis_date = data.get("analysis_date", "")
    time_range = data.get("time_range", {})
    start_date = time_range.get("start", "")
    end_date = time_range.get("end", "")

    total_reviews = data.get("total_reviews", 0)
    overall_avg_rating = float(data.get("overall_avg_rating", 0))
    sentiment_breakdown = data.get("sentiment_breakdown", {})
    positive_ratio = float(sentiment_breakdown.get("positive", 0))
    neutral_ratio = float(sentiment_breakdown.get("neutral", 0))
    negative_ratio = float(sentiment_breakdown.get("negative", 0))

    monthly_data = data.get("monthly_data", [])
    complaint_themes = data.get("complaint_themes", [])
    action_items = data.get("action_items", [])
    insights = data.get("insights", [])
    executive_summary = data.get("executive_summary", "")

    top_complaint = complaint_themes[0]["theme"] if complaint_themes else "N/A"

    # Overall rating distribution (for donut)
    total_rating_counts = {str(i): 0 for i in range(1, 6)}
    for m in monthly_data:
        for key, val in m.get("rating_counts", {}).items():
            if key in total_rating_counts:
                total_rating_counts[key] += int(val)

    # Monthly table rows
    table_rows_html = []
    for m in monthly_data:
        month = m.get("month", "")
        review_count = int(m.get("review_count", 0))
        avg_rating = float(m.get("avg_rating", 0))
        rating_counts = m.get("rating_counts", {})
        sentiment_pct = m.get("sentiment_pct", {})

        pos = float(sentiment_pct.get("positive", 0))
        neu = float(sentiment_pct.get("neutral", 0))
        neg = float(sentiment_pct.get("negative", 0))

        stars = stars_from_rating(avg_rating)
        rating_breakdown = " ".join([f"★{i}:{rating_counts.get(str(i), 0)}" for i in range(1, 6)])

        table_rows_html.append(
            f"""
            <tr>
              <td data-sort="{escape_html(month)}">{escape_html(month)}</td>
              <td data-sort="{review_count}">{review_count}</td>
              <td data-sort="{avg_rating:.2f}">{avg_rating:.2f}</td>
              <td data-sort="{avg_rating:.2f}"><span class=\"stars\">{stars}</span></td>
              <td data-sort="{neg:.2f}">
                <div class=\"sentiment-bar\">
                  <span class=\"seg pos\" style=\"width:{pos:.2f}%\"></span>
                  <span class=\"seg neu\" style=\"width:{neu:.2f}%\"></span>
                  <span class=\"seg neg\" style=\"width:{neg:.2f}%\"></span>
                </div>
                <div class=\"sentiment-legend\">{pos:.1f}% / {neu:.1f}% / {neg:.1f}%</div>
              </td>
              <td data-sort="{review_count}">{escape_html(rating_breakdown)}</td>
            </tr>
            """.strip()
        )

    # Insights cards
    insight_cards = []
    for idx, insight in enumerate(insights[:6]):
        title = insight.get("title", f"Insight {idx + 1}")
        quote = insight.get("quote", "")
        icon = "💡" if idx % 3 == 0 else "⚠️" if idx % 3 == 1 else "🔎"
        insight_cards.append(
            f"""
            <div class=\"insight-card\">
              <div class=\"insight-icon\">{icon}</div>
              <div>
                <h4>{escape_html(title)}</h4>
                <p>\"{escape_html(quote)}\"</p>
              </div>
            </div>
            """.strip()
        )

    if not insight_cards:
        insight_cards.append(
            """
            <div class=\"insight-card\">
              <div class=\"insight-icon\">💡</div>
              <div>
                <h4>No major insight extracted</h4>
                <p>Not enough review detail was available to extract a representative quote.</p>
              </div>
            </div>
            """.strip()
        )

    # Action items
    action_rows = []
    for i, item in enumerate(action_items, start=1):
        priority = item.get("priority", "Low")
        rec = item.get("recommendation", "")
        theme = item.get("addresses_theme", "")
        action_rows.append(
            f"""
            <li class=\"action-item\">
              <span class=\"action-index\">{i}.</span>
              <div class=\"action-content\">
                <div class=\"action-head\">
                  <span class=\"priority-pill {priority_class(priority)}\">{escape_html(priority)}</span>
                  <span class=\"action-theme\">{escape_html(theme)}</span>
                </div>
                <p>{escape_html(rec)}</p>
              </div>
            </li>
            """.strip()
        )

    if not action_rows:
        action_rows.append(
            """
            <li class=\"action-item\">
              <span class=\"action-index\">1.</span>
              <div class=\"action-content\"><p>No action items found.</p></div>
            </li>
            """.strip()
        )

    monthly_json = json.dumps(monthly_data)
    complaints_json = json.dumps(complaint_themes)
    total_rating_json = json.dumps(total_rating_counts)
    sentiment_breakdown_json = json.dumps(
        {
            "positive": round(positive_ratio * 100, 1),
            "neutral": round(neutral_ratio * 100, 1),
            "negative": round(negative_ratio * 100, 1),
        }
    )

    return f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Customer Review Dashboard — {escape_html(product_name)}</title>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js\"></script>
  <style>
    :root {{
      --bg: #0a0e1a;
      --bg-secondary: #121829;
      --card: #1a2035;
      --text: #e8ecf4;
      --text-secondary: #8892a8;
      --text-muted: #5a6580;
      --border: #2a3555;
      --accent1: #f97316;
      --accent2: #fb923c;
      --accent3: #fbbf24;
      --green: #22c55e;
      --yellow: #eab308;
      --red: #ef4444;
      --blue: #3b82f6;
      --radius: 12px;
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
    }}

    .container {{
      max-width: 1260px;
      margin: 0 auto;
      padding: 20px;
    }}

    .section {{
      animation: fadeSlide 500ms ease both;
      margin-bottom: 20px;
    }}

    @keyframes fadeSlide {{
      from {{ opacity: 0; transform: translateY(20px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
      transition: transform .2s ease, box-shadow .2s ease;
    }}

    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.34);
    }}

    .header {{
      position: relative;
      overflow: hidden;
      padding: 24px;
      background: linear-gradient(140deg, #0f172a 0%, #111827 50%, #1f2937 100%);
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
    }}

    .header::before {{
      content: '';
      position: absolute;
      width: 320px;
      height: 320px;
      right: -120px;
      top: -120px;
      background: radial-gradient(circle, rgba(251, 146, 60, 0.33), rgba(251, 146, 60, 0));
      pointer-events: none;
    }}

    .title {{
      margin: 0;
      font-size: 2rem;
      font-weight: 800;
      background: linear-gradient(90deg, var(--accent1), var(--accent2), var(--accent3));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .subtitle {{
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      color: var(--text-secondary);
      font-size: 0.92rem;
    }}

    .badge {{
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--bg-secondary);
      color: var(--text-secondary);
      text-decoration: none;
    }}

    .stats-cluster {{
      display: grid;
      grid-template-columns: repeat(3, minmax(120px, 1fr));
      gap: 8px;
      align-content: start;
      z-index: 1;
    }}

    .stat-box {{
      background: rgba(26, 32, 53, 0.85);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px;
      text-align: center;
    }}

    .stat-box .v {{ font-size: 1.1rem; font-weight: 700; }}
    .stat-box .k {{ color: var(--text-muted); font-size: 0.78rem; }}

    .sticky-filter {{
      position: sticky;
      top: 8px;
      z-index: 50;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      background: rgba(18, 24, 41, 0.72);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      backdrop-filter: blur(12px);
    }}

    .sticky-filter select,
    .sticky-filter button {{
      background: var(--card);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 0.9rem;
    }}

    .sticky-filter button {{
      cursor: pointer;
      background: linear-gradient(90deg, var(--accent1), var(--accent2));
      color: #111827;
      font-weight: 700;
      border: none;
    }}

    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(160px, 1fr));
      gap: 12px;
    }}

    .kpi {{
      padding: 14px;
      border-top: 3px solid var(--accent2);
    }}

    .kpi.red {{ border-top-color: var(--red); }}
    .kpi.yellow {{ border-top-color: var(--yellow); }}
    .kpi.green {{ border-top-color: var(--green); }}
    .kpi.blue {{ border-top-color: var(--blue); }}

    .kpi .label {{ color: var(--text-secondary); font-size: 0.82rem; }}
    .kpi .value {{ font-size: 1.35rem; font-weight: 700; margin-top: 6px; }}

    .summary-card {{
      padding: 18px;
      border-left: 4px solid var(--accent2);
    }}

    .summary-card p {{ margin: 0; color: var(--text-secondary); }}

    .charts-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}

    .chart-card {{
      padding: 12px;
      min-height: 360px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .chart-card h3 {{
      margin: 0 0 10px;
      font-size: 1rem;
      color: var(--text-secondary);
      flex: 0 0 auto;
    }}
    .chart-card canvas {{
      display: block;
      width: 100% !important;
      height: 290px !important;
      flex: 1 1 auto;
      min-height: 0;
    }}

    .table-card {{ padding: 12px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 10px;
      text-align: left;
      vertical-align: top;
      font-size: 0.9rem;
      word-break: break-word;
    }}
    th {{
      color: var(--text-secondary);
      cursor: pointer;
      position: sticky;
      top: 0;
      background: var(--card);
    }}

    .stars {{ color: #fbbf24; letter-spacing: 1px; }}

    .sentiment-bar {{
      display: flex;
      height: 10px;
      border-radius: 999px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: #10162a;
    }}

    .seg.pos {{ background: var(--green); }}
    .seg.neu {{ background: var(--yellow); }}
    .seg.neg {{ background: var(--red); }}

    .sentiment-legend {{
      color: var(--text-muted);
      font-size: 0.76rem;
      margin-top: 4px;
    }}

    .deep-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(240px, 1fr));
      gap: 12px;
    }}

    .insights-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(280px, 1fr));
      gap: 12px;
    }}

    .insight-card {{
      display: grid;
      grid-template-columns: 34px 1fr;
      gap: 10px;
      padding: 12px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
    }}

    .insight-icon {{ font-size: 1.2rem; margin-top: 2px; }}
    .insight-card h4 {{ margin: 0 0 6px; font-size: 0.95rem; }}
    .insight-card p {{
      margin: 0;
      color: var(--text-secondary);
      font-size: 0.86rem;
      overflow-wrap: anywhere;
    }}

    .actions-card {{ padding: 14px; }}
    .actions-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
    .action-item {{ display: grid; grid-template-columns: 26px 1fr; gap: 8px; }}
    .action-index {{ color: var(--text-secondary); margin-top: 1px; }}
    .action-content {{ border: 1px solid var(--border); border-radius: 10px; padding: 10px; background: var(--bg-secondary); }}
    .action-content p {{ margin: 6px 0 0; color: var(--text-secondary); }}
    .action-head {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .action-theme {{ color: var(--text-muted); font-size: 0.82rem; }}

    .priority-pill {{
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 0.78rem;
      font-weight: 700;
    }}

    .priority-high {{ border-color: var(--red); color: #fecaca; }}
    .priority-medium {{ border-color: var(--yellow); color: #fde68a; }}
    .priority-low {{ border-color: var(--green); color: #bbf7d0; }}

    @media (max-width: 1100px) {{
      .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .deep-grid {{ grid-template-columns: 1fr; }}
      .insights-grid {{ grid-template-columns: 1fr; }}
      .header {{ grid-template-columns: 1fr; }}
      .stats-cluster {{ grid-template-columns: repeat(3, 1fr); }}
    }}

    @media (max-width: 900px) {{
      .charts-grid {{ grid-template-columns: 1fr; }}
      .chart-card {{ min-height: 320px; }}
      .chart-card canvas {{ height: 250px !important; }}
    }}

    @media (max-width: 640px) {{
      .container {{ padding: 14px; }}
      .sticky-filter {{
        flex-wrap: wrap;
        align-items: stretch;
      }}
      .sticky-filter select,
      .sticky-filter button {{
        width: 100%;
      }}
      .stats-cluster {{ grid-template-columns: 1fr; }}
      .kpi-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"container\">
    <section class=\"section card header\">
      <div>
        <h1 class=\"title\">Customer Review Intelligence Dashboard</h1>
        <div style=\"margin-top:6px;font-size:1rem;font-weight:600;\">{escape_html(product_name)}</div>
        <div class=\"subtitle\">
          <a class=\"badge\" href=\"{escape_html(source_url)}\" target=\"_blank\" rel=\"noreferrer\">Source URL</a>
          <span class=\"badge\">Period: {escape_html(start_date)} → {escape_html(end_date)}</span>
          <span class=\"badge\">Generated: {escape_html(analysis_date)}</span>
        </div>
      </div>
      <div class=\"stats-cluster\">
        <div class=\"stat-box\"><div class=\"v\">{total_reviews}</div><div class=\"k\">Total Reviews</div></div>
        <div class=\"stat-box\"><div class=\"v\">{overall_avg_rating:.2f} <span class=\"stars\">{stars_from_rating(overall_avg_rating)}</span></div><div class=\"k\">Avg Rating</div></div>
        <div class=\"stat-box\"><div class=\"v\">{pct(positive_ratio)}</div><div class=\"k\">Positive %</div></div>
      </div>
    </section>

    <section class=\"section sticky-filter\">
      <strong style=\"color:var(--text-secondary);font-size:0.9rem;\">Month filter</strong>
      <select id=\"monthFilter\">
        <option value=\"all\">All months</option>
      </select>
      <button id=\"resetFilter\">Reset</button>
    </section>

    <section class=\"section kpi-grid\">
      <div class=\"card kpi\"><div class=\"label\">Avg Rating</div><div class=\"value\">{overall_avg_rating:.2f}</div></div>
      <div class=\"card kpi red\"><div class=\"label\">Negative %</div><div class=\"value\">{pct(negative_ratio)}</div></div>
      <div class=\"card kpi yellow\"><div class=\"label\">Neutral %</div><div class=\"value\">{pct(neutral_ratio)}</div></div>
      <div class=\"card kpi green\"><div class=\"label\">Positive %</div><div class=\"value\">{pct(positive_ratio)}</div></div>
      <div class=\"card kpi blue\"><div class=\"label\">Top complaint</div><div class=\"value\" style=\"font-size:1rem;\">{escape_html(top_complaint)}</div></div>
    </section>

    <section class=\"section card summary-card\">
      <p>{escape_html(executive_summary)}</p>
    </section>

    <section class=\"section charts-grid\">
      <div class=\"card chart-card\"><h3>Average Rating Trend</h3><canvas id=\"ratingLine\"></canvas></div>
      <div class=\"card chart-card\"><h3>Review Volume</h3><canvas id=\"volumeBar\"></canvas></div>
      <div class=\"card chart-card\"><h3>Rating Segmentation (★1–★5)</h3><canvas id=\"ratingStacked\"></canvas></div>
      <div class=\"card chart-card\"><h3>Sentiment Trend (%)</h3><canvas id=\"sentimentLine\"></canvas></div>
    </section>

    <section class=\"section card table-card\">
      <h3 style=\"margin:0 0 10px; color:var(--text-secondary);\">Monthly Data Table</h3>
      <table id=\"monthlyTable\">
        <thead>
          <tr>
            <th data-col=\"0\">Month</th>
            <th data-col=\"1\">Reviews</th>
            <th data-col=\"2\">Avg Rating</th>
            <th data-col=\"3\">Stars</th>
            <th data-col=\"4\">Sentiment Bar</th>
            <th data-col=\"5\">Rating Breakdown</th>
          </tr>
        </thead>
        <tbody>
          {''.join(table_rows_html)}
        </tbody>
      </table>
    </section>

    <section class=\"section deep-grid\">
      <div class=\"card chart-card\"><h3>Sentiment Split</h3><canvas id=\"sentimentDonut\"></canvas></div>
      <div class=\"card chart-card\"><h3>Rating Distribution</h3><canvas id=\"ratingDonut\"></canvas></div>
      <div class=\"card chart-card\"><h3>Top Complaints</h3><canvas id=\"complaintsBar\"></canvas></div>
    </section>

    <section class=\"section\">
      <h3 style=\"margin:0 0 10px; color:var(--text-secondary);\">Key Insights</h3>
      <div class=\"insights-grid\">{''.join(insight_cards)}</div>
    </section>

    <section class=\"section card actions-card\">
      <h3 style=\"margin:0 0 10px; color:var(--text-secondary);\">Action Items</h3>
      <ol class=\"actions-list\">{''.join(action_rows)}</ol>
    </section>
  </div>

  <script>
    const MONTHLY_DATA = {monthly_json};
    const COMPLAINT_THEMES = {complaints_json};
    const SENTIMENT_SPLIT = {sentiment_breakdown_json};
    const RATING_TOTAL = {total_rating_json};
    const OVERALL_AVG = {overall_avg_rating:.2f};

    const monthFilter = document.getElementById('monthFilter');
    const resetBtn = document.getElementById('resetFilter');

    for (const m of MONTHLY_DATA) {{
      const opt = document.createElement('option');
      opt.value = m.month;
      opt.textContent = m.month;
      monthFilter.appendChild(opt);
    }}

    const charts = {{}};

    function destroyIfExists(name) {{
      if (charts[name]) {{ charts[name].destroy(); }}
    }}

    function filteredMonthly() {{
      const selected = monthFilter.value;
      if (selected === 'all') return MONTHLY_DATA;
      return MONTHLY_DATA.filter(m => m.month === selected);
    }}

    function makeTrendCharts() {{
      const data = filteredMonthly();
      const labels = data.map(d => d.month);

      const avg = data.map(d => d.avg_rating);
      const volume = data.map(d => d.review_count);
      const s1 = data.map(d => d.rating_counts['1'] || 0);
      const s2 = data.map(d => d.rating_counts['2'] || 0);
      const s3 = data.map(d => d.rating_counts['3'] || 0);
      const s4 = data.map(d => d.rating_counts['4'] || 0);
      const s5 = data.map(d => d.rating_counts['5'] || 0);

      const pos = data.map(d => d.sentiment_pct.positive || 0);
      const neu = data.map(d => d.sentiment_pct.neutral || 0);
      const neg = data.map(d => d.sentiment_pct.negative || 0);

      destroyIfExists('ratingLine');
      const ratingCtx = document.getElementById('ratingLine').getContext('2d');
      const grad = ratingCtx.createLinearGradient(0, 0, 0, 220);
      grad.addColorStop(0, 'rgba(251, 146, 60, 0.35)');
      grad.addColorStop(1, 'rgba(251, 146, 60, 0)');
      charts.ratingLine = new Chart(ratingCtx, {{
        type: 'line',
        data: {{
          labels,
          datasets: [
            {{
              label: 'Avg rating',
              data: avg,
              borderColor: '#fb923c',
              backgroundColor: grad,
              fill: true,
              tension: 0.25,
              pointRadius: 3,
            }},
            {{
              label: 'Overall avg',
              data: labels.map(() => OVERALL_AVG),
              borderColor: '#8892a8',
              borderDash: [5, 5],
              fill: false,
              pointRadius: 0,
            }}
          ]
        }},
        options: commonOptions(0, 5)
      }});

      destroyIfExists('volumeBar');
      charts.volumeBar = new Chart(document.getElementById('volumeBar'), {{
        type: 'bar',
        data: {{ labels, datasets: [{{ label: 'Reviews', data: volume, backgroundColor: '#3b82f6' }}] }},
        options: commonOptions(0, undefined)
      }});

      destroyIfExists('ratingStacked');
      charts.ratingStacked = new Chart(document.getElementById('ratingStacked'), {{
        type: 'bar',
        data: {{
          labels,
          datasets: [
            {{ label: '★1', data: s1, backgroundColor: '#dc2626' }},
            {{ label: '★2', data: s2, backgroundColor: '#f97316' }},
            {{ label: '★3', data: s3, backgroundColor: '#eab308' }},
            {{ label: '★4', data: s4, backgroundColor: '#22c55e' }},
            {{ label: '★5', data: s5, backgroundColor: '#38bdf8' }},
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#e8ecf4' }} }} }},
          scales: {{
            x: {{ stacked: true, ticks: {{ color: '#8892a8' }}, grid: {{ color: '#24314f' }} }},
            y: {{ stacked: true, ticks: {{ color: '#8892a8' }}, grid: {{ color: '#24314f' }} }}
          }}
        }}
      }});

      destroyIfExists('sentimentLine');
      charts.sentimentLine = new Chart(document.getElementById('sentimentLine'), {{
        type: 'line',
        data: {{
          labels,
          datasets: [
            {{ label: 'Positive %', data: pos, borderColor: '#22c55e', tension: 0.25 }},
            {{ label: 'Neutral %', data: neu, borderColor: '#eab308', tension: 0.25 }},
            {{ label: 'Negative %', data: neg, borderColor: '#ef4444', tension: 0.25 }}
          ]
        }},
        options: commonOptions(0, 100)
      }});
    }}

    function commonOptions(minY, maxY) {{
      return {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ labels: {{ color: '#e8ecf4' }} }}
        }},
        scales: {{
          x: {{ ticks: {{ color: '#8892a8' }}, grid: {{ color: '#24314f' }} }},
          y: {{
            min: minY,
            max: maxY,
            ticks: {{ color: '#8892a8' }},
            grid: {{ color: '#24314f' }}
          }}
        }}
      }};
    }}

    function makeDeepCharts() {{
      charts.sentimentDonut = new Chart(document.getElementById('sentimentDonut'), {{
        type: 'doughnut',
        data: {{
          labels: ['Positive', 'Neutral', 'Negative'],
          datasets: [{{
            data: [SENTIMENT_SPLIT.positive, SENTIMENT_SPLIT.neutral, SENTIMENT_SPLIT.negative],
            backgroundColor: ['#22c55e', '#eab308', '#ef4444']
          }}]
        }},
        options: {{ plugins: {{ legend: {{ labels: {{ color: '#e8ecf4' }} }} }} }}
      }});

      charts.ratingDonut = new Chart(document.getElementById('ratingDonut'), {{
        type: 'doughnut',
        data: {{
          labels: ['★1', '★2', '★3', '★4', '★5'],
          datasets: [{{
            data: [RATING_TOTAL['1'], RATING_TOTAL['2'], RATING_TOTAL['3'], RATING_TOTAL['4'], RATING_TOTAL['5']],
            backgroundColor: ['#dc2626', '#f97316', '#eab308', '#22c55e', '#38bdf8']
          }}]
        }},
        options: {{ plugins: {{ legend: {{ labels: {{ color: '#e8ecf4' }} }} }} }}
      }});

      charts.complaintsBar = new Chart(document.getElementById('complaintsBar'), {{
        type: 'bar',
        data: {{
          labels: COMPLAINT_THEMES.slice(0, 7).map(t => t.theme),
          datasets: [{{
            label: 'Mentions',
            data: COMPLAINT_THEMES.slice(0, 7).map(t => t.count),
            backgroundColor: '#fb923c'
          }}]
        }},
        options: {{
          indexAxis: 'y',
          plugins: {{ legend: {{ labels: {{ color: '#e8ecf4' }} }} }},
          scales: {{
            x: {{ ticks: {{ color: '#8892a8' }}, grid: {{ color: '#24314f' }} }},
            y: {{ ticks: {{ color: '#8892a8' }}, grid: {{ color: '#24314f' }} }}
          }}
        }}
      }});
    }}

    function setupTableSort() {{
      const table = document.getElementById('monthlyTable');
      const headers = table.querySelectorAll('th');
      let state = {{ col: 0, asc: true }};

      headers.forEach((th, idx) => {{
        th.addEventListener('click', () => {{
          const tbody = table.querySelector('tbody');
          const rows = [...tbody.querySelectorAll('tr')];
          const asc = state.col === idx ? !state.asc : true;
          state = {{ col: idx, asc }};

          rows.sort((a, b) => {{
            const av = a.children[idx].dataset.sort || a.children[idx].innerText;
            const bv = b.children[idx].dataset.sort || b.children[idx].innerText;
            const an = Number(av);
            const bn = Number(bv);
            const bothNumeric = !Number.isNaN(an) && !Number.isNaN(bn);
            if (bothNumeric) {{
              return asc ? an - bn : bn - an;
            }}
            return asc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
          }});

          rows.forEach(r => tbody.appendChild(r));
        }});
      }});
    }}

    monthFilter.addEventListener('change', makeTrendCharts);
    resetBtn.addEventListener('click', () => {{ monthFilter.value = 'all'; makeTrendCharts(); }});

    makeTrendCharts();
    makeDeepCharts();
    setupTableSort();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate customer review HTML dashboard")
    parser.add_argument("--data", required=True, help="Path to analysis_results.json")
    parser.add_argument("--output", required=True, help="Path to output HTML file")
    args = parser.parse_args()

    data_path = Path(args.data)
    output_path = Path(args.output)

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    html = render_html(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Generated report: {output_path.resolve()}")


if __name__ == "__main__":
    main()
