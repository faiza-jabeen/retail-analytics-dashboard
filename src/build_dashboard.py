import json

with open("outputs/dashboard_data.json") as f:
    D = json.load(f)

k = D["kpis"]
monthly = D["monthly"]
category = D["category"]
city = D["city"]
channel = D["channel"]
products = D["top_products"]
retention = D["retention"]
segments = D["segments"]


def fmt_pkr(v):
    if v >= 1e6:
        return f"{v/1e6:.1f}M"
    if v >= 1e3:
        return f"{v/1e3:.0f}K"
    return f"{v:.0f}"


html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Retail Analytics · Sales &amp; Customer Performance</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:      #0B0E14;
    --panel:    #141922;
    --line:     #232B38;
    --dim:      #6C7A8F;
    --text:     #D8DEE9;
    --bright:   #F2F5F9;
    --signal:   #4ADE80;
    --warn:     #FBBF24;
    --alert:    #F87171;
    --cool:     #60A5FA;
    --violet:   #A78BFA;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--ink);
    color: var(--text);
    font-family: 'Archivo', system-ui, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    padding: 28px 22px 60px;
    -webkit-font-smoothing: antialiased;
  }}

  .wrap {{ max-width: 1240px; margin: 0 auto; }}

  /* ---------- masthead ---------- */
  header {{
    display: flex; align-items: baseline; justify-content: space-between;
    flex-wrap: wrap; gap: 12px;
    padding-bottom: 16px; margin-bottom: 24px;
    border-bottom: 1px solid var(--line);
  }}
  h1 {{
    font-size: 19px; font-weight: 700; letter-spacing: -0.01em;
    color: var(--bright);
  }}
  h1 span {{ color: var(--dim); font-weight: 400; }}
  .period {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: var(--dim);
    letter-spacing: 0.06em; text-transform: uppercase;
  }}

  /* ---------- KPI strip ---------- */
  .kpis {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1px;
    background: var(--line);
    border: 1px solid var(--line);
    margin-bottom: 26px;
  }}
  .kpi {{ background: var(--panel); padding: 16px 18px; }}
  .kpi-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.09em; text-transform: uppercase;
    color: var(--dim); margin-bottom: 8px;
  }}
  .kpi-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 26px; font-weight: 700; color: var(--bright);
    letter-spacing: -0.02em; line-height: 1.1;
  }}
  .kpi-value .unit {{ font-size: 14px; color: var(--dim); font-weight: 400; }}
  .kpi-sub {{ font-size: 11px; color: var(--dim); margin-top: 5px; }}
  .pos {{ color: var(--signal); }}
  .neg {{ color: var(--alert); }}

  /* ---------- grid ---------- */
  .grid {{ display: grid; gap: 18px; margin-bottom: 18px; }}
  .g-2 {{ grid-template-columns: 1.6fr 1fr; }}
  .g-3 {{ grid-template-columns: repeat(3, 1fr); }}
  @media (max-width: 900px) {{
    .g-2, .g-3 {{ grid-template-columns: 1fr; }}
  }}

  .card {{
    background: var(--panel);
    border: 1px solid var(--line);
    padding: 18px 20px 20px;
  }}
  .card-head {{
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 16px;
  }}
  .card-title {{
    font-size: 13px; font-weight: 600; color: var(--bright);
    letter-spacing: 0.01em;
  }}
  .card-note {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: var(--dim); letter-spacing: 0.04em;
  }}
  .chart {{ position: relative; height: 230px; }}
  .chart.tall {{ height: 280px; }}

  /* ---------- tables ---------- */
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.07em; text-transform: uppercase;
    color: var(--dim); font-weight: 500;
    text-align: right; padding: 0 0 9px;
    border-bottom: 1px solid var(--line);
  }}
  th:first-child {{ text-align: left; }}
  td {{
    padding: 9px 0; font-size: 13px;
    border-bottom: 1px solid rgba(35,43,56,0.5);
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
  }}
  td:first-child {{
    text-align: left; font-family: 'Archivo', sans-serif;
    color: var(--bright);
  }}
  tr:last-child td {{ border-bottom: none; }}
  .bar-cell {{ position: relative; }}
  .bar {{
    position: absolute; left: 0; top: 50%; transform: translateY(-50%);
    height: 3px; background: var(--cool); opacity: 0.5;
  }}

  /* ---------- cohort heatmap ---------- */
  .cohort {{ overflow-x: auto; }}
  .cohort table {{ min-width: 620px; }}
  .cohort td, .cohort th {{
    text-align: center; padding: 5px 3px;
    font-size: 11px; border: none;
  }}
  .cohort td:first-child, .cohort th:first-child {{
    text-align: left; padding-right: 12px;
    color: var(--dim); font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
  }}
  .cell {{
    display: block; padding: 6px 2px; border-radius: 2px;
    color: var(--bright); font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
  }}

  /* ---------- segments ---------- */
  .seg {{
    display: flex; align-items: center; gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid rgba(35,43,56,0.5);
  }}
  .seg:last-child {{ border-bottom: none; }}
  .seg-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .seg-name {{ flex: 1; font-size: 13px; color: var(--bright); }}
  .seg-track {{
    flex: 1.4; height: 5px; background: rgba(255,255,255,0.05);
    border-radius: 3px; overflow: hidden;
  }}
  .seg-fill {{ height: 100%; border-radius: 3px; }}
  .seg-pct {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: var(--text); width: 46px; text-align: right;
  }}

  .callout {{
    margin-top: 14px; padding: 12px 14px;
    background: rgba(248,113,113,0.07);
    border-left: 2px solid var(--alert);
    font-size: 12.5px; line-height: 1.55; color: var(--text);
  }}
  .callout strong {{ color: var(--bright); font-weight: 600; }}

  footer {{
    margin-top: 34px; padding-top: 16px;
    border-top: 1px solid var(--line);
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
    font-size: 11.5px; color: var(--dim);
  }}
  footer a {{ color: var(--cool); text-decoration: none; }}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>Retail Analytics <span>/ sales &amp; customer performance</span></h1>
    <div class="period">Jan 2023 &mdash; Dec 2024 &middot; 26,657 orders</div>
  </header>

  <!-- KPI STRIP -->
  <div class="kpis">
    <div class="kpi">
      <div class="kpi-label">Net Revenue</div>
      <div class="kpi-value">{fmt_pkr(k['total_revenue'])}<span class="unit"> PKR</span></div>
      <div class="kpi-sub">after returns &amp; discounts</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Gross Profit</div>
      <div class="kpi-value">{fmt_pkr(k['gross_profit'])}<span class="unit"> PKR</span></div>
      <div class="kpi-sub pos">{k['margin_pct']:.1f}% margin</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Avg Order Value</div>
      <div class="kpi-value">{k['avg_order_value']:,.0f}<span class="unit"> PKR</span></div>
      <div class="kpi-sub">{k['orders_per_customer']:.1f} orders / customer</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Return Rate</div>
      <div class="kpi-value">{k['return_rate_pct']:.1f}<span class="unit">%</span></div>
      <div class="kpi-sub neg">&minus;{fmt_pkr(k['revenue_lost_to_returns'])} PKR lost</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Customers</div>
      <div class="kpi-value">{k['unique_customers']:,}</div>
      <div class="kpi-sub">{retention['avg_month1']:.0f}% return in month 1</div>
    </div>
  </div>

  <!-- TREND + CATEGORY -->
  <div class="grid g-2">
    <div class="card">
      <div class="card-head">
        <div class="card-title">Revenue &amp; profit by month</div>
        <div class="card-note">PKR millions</div>
      </div>
      <div class="chart tall"><canvas id="trend"></canvas></div>
    </div>
    <div class="card">
      <div class="card-head">
        <div class="card-title">Category mix</div>
        <div class="card-note">share of revenue</div>
      </div>
      <div class="chart tall"><canvas id="cat"></canvas></div>
    </div>
  </div>

  <!-- CHANNEL + CITY + PRODUCTS -->
  <div class="grid g-3">
    <div class="card">
      <div class="card-head">
        <div class="card-title">Channel</div>
        <div class="card-note">AOV</div>
      </div>
      <table>
        <thead><tr><th>Source</th><th>Revenue</th><th>AOV</th></tr></thead>
        <tbody>
        {''.join(f'''<tr>
          <td>{c['channel']}</td>
          <td>{fmt_pkr(c['revenue'])}</td>
          <td>{c['aov']:,.0f}</td>
        </tr>''' for c in channel)}
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="card-head">
        <div class="card-title">City</div>
        <div class="card-note">top 5</div>
      </div>
      <table>
        <thead><tr><th>Market</th><th>Revenue</th><th>Cust.</th></tr></thead>
        <tbody>
        {''.join(f'''<tr>
          <td>{c['city']}</td>
          <td>{fmt_pkr(c['revenue'])}</td>
          <td>{c['customers']}</td>
        </tr>''' for c in city[:5])}
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="card-head">
        <div class="card-title">Top products</div>
        <div class="card-note">by revenue</div>
      </div>
      <table>
        <thead><tr><th>Item</th><th>Revenue</th><th>Units</th></tr></thead>
        <tbody>
        {''.join(f'''<tr>
          <td>{p['product']}</td>
          <td>{fmt_pkr(p['revenue'])}</td>
          <td>{p['units']:,}</td>
        </tr>''' for p in products[:5])}
        </tbody>
      </table>
    </div>
  </div>

  <!-- COHORT + SEGMENTS -->
  <div class="grid g-2">
    <div class="card">
      <div class="card-head">
        <div class="card-title">Cohort retention</div>
        <div class="card-note">% of cohort ordering again</div>
      </div>
      <div class="cohort">
        <table>
          <thead>
            <tr>
              <th>Cohort</th>
              {''.join(f'<th>M{i}</th>' for i in range(0, 12))}
            </tr>
          </thead>
          <tbody id="cohort-body"></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <div class="card-title">Customer segments</div>
        <div class="card-note">RFM &middot; share of revenue</div>
      </div>
      <div id="segments"></div>
      <div class="callout">
        <strong>At Risk customers hold {[s for s in segments if s['segment']=='At Risk'][0]['revenue_share_pct']:.0f}% of revenue</strong>
        but haven't ordered recently. Winning back this group is worth more than
        acquiring an equivalent number of new customers, who contribute only
        {[s for s in segments if s['segment']=='New / Promising'][0]['revenue_share_pct']:.0f}%.
      </div>
    </div>
  </div>

  <footer>
    <div>Built by Faiza Jabeen &middot; Python &middot; pandas &middot; Chart.js</div>
    <div>Synthetic data modelled on Pakistani e-commerce patterns</div>
  </footer>

</div>

<script>
const DATA = {json.dumps({
    'monthly': monthly,
    'category': category,
    'retention': retention,
    'segments': segments,
}, default=str)};

const CSS = getComputedStyle(document.documentElement);
const C = n => CSS.getPropertyValue(n).trim();

Chart.defaults.color = C('--dim');
Chart.defaults.borderColor = C('--line');
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 10;

/* ---- monthly trend ---- */
new Chart(document.getElementById('trend'), {{
  type: 'bar',
  data: {{
    labels: DATA.monthly.map(m => m.year_month.slice(2)),
    datasets: [
      {{
        label: 'Revenue',
        data: DATA.monthly.map(m => m.revenue / 1e6),
        backgroundColor: 'rgba(96,165,250,0.28)',
        borderColor: C('--cool'),
        borderWidth: 1,
        order: 2,
      }},
      {{
        label: 'Profit',
        data: DATA.monthly.map(m => m.profit / 1e6),
        type: 'line',
        borderColor: C('--signal'),
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
        order: 1,
      }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{
        position: 'top', align: 'end',
        labels: {{ boxWidth: 8, boxHeight: 8, padding: 12, usePointStyle: true }}
      }},
      tooltip: {{
        backgroundColor: '#0B0E14',
        borderColor: C('--line'), borderWidth: 1,
        titleColor: C('--bright'), bodyColor: C('--text'),
        padding: 10, displayColors: true, boxWidth: 8, boxHeight: 8,
        callbacks: {{
          label: c => ` ${{c.dataset.label}}: ${{c.parsed.y.toFixed(1)}}M PKR`
        }}
      }}
    }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 0, autoSkipPadding: 8 }} }},
      y: {{
        grid: {{ color: 'rgba(35,43,56,0.6)' }},
        ticks: {{ callback: v => v + 'M' }},
        beginAtZero: true,
      }}
    }}
  }}
}});

/* ---- category doughnut ---- */
const catColors = [C('--cool'), C('--violet'), C('--signal'), C('--warn'), C('--alert')];
new Chart(document.getElementById('cat'), {{
  type: 'doughnut',
  data: {{
    labels: DATA.category.map(c => c.category),
    datasets: [{{
      data: DATA.category.map(c => c.revenue),
      backgroundColor: catColors,
      borderColor: C('--panel'),
      borderWidth: 2,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    cutout: '58%',
    plugins: {{
      legend: {{
        position: 'bottom',
        labels: {{ boxWidth: 8, boxHeight: 8, padding: 10, usePointStyle: true, font: {{ size: 10 }} }}
      }},
      tooltip: {{
        backgroundColor: '#0B0E14',
        borderColor: C('--line'), borderWidth: 1,
        titleColor: C('--bright'), bodyColor: C('--text'), padding: 10,
        callbacks: {{
          label: c => {{
            const cat = DATA.category[c.dataIndex];
            const pct = (cat.revenue / DATA.category.reduce((a,b)=>a+b.revenue,0) * 100).toFixed(1);
            return [` ${{(cat.revenue/1e6).toFixed(1)}}M PKR (${{pct}}%)`,
                    ` margin ${{cat.margin_pct.toFixed(1)}}%`];
          }}
        }}
      }}
    }}
  }}
}});

/* ---- cohort heatmap ---- */
const R = DATA.retention;
const body = document.getElementById('cohort-body');
R.matrix.forEach((row, i) => {{
  const tr = document.createElement('tr');
  const label = document.createElement('td');
  label.textContent = R.cohorts[i];
  tr.appendChild(label);

  for (let j = 0; j < 12; j++) {{
    const td = document.createElement('td');
    const v = row[j];
    if (v === undefined || v === null) {{
      td.innerHTML = '<span style="color:#2A3444">·</span>';
    }} else {{
      const span = document.createElement('span');
      span.className = 'cell';
      // opacity scales with retention; month 0 is always 100%
      const alpha = j === 0 ? 0.85 : Math.min(0.8, 0.08 + (v / 100) * 1.3);
      span.style.background = `rgba(74,222,128,${{alpha}})`;
      span.style.color = alpha > 0.45 ? '#0B0E14' : '#D8DEE9';
      span.textContent = v.toFixed(0);
      td.appendChild(span);
    }}
    tr.appendChild(td);
  }}
  body.appendChild(tr);
}});

/* ---- segments ---- */
const segColors = {{
  'Champions':       C('--signal'),
  'Loyal':           C('--cool'),
  'At Risk':         C('--warn'),
  'Cannot Lose':     C('--alert'),
  'New / Promising': C('--violet'),
  'Hibernating':     '#4A5768',
}};
const segBox = document.getElementById('segments');
const maxShare = Math.max(...DATA.segments.map(s => s.revenue_share_pct));

DATA.segments.forEach(s => {{
  const row = document.createElement('div');
  row.className = 'seg';
  const col = segColors[s.segment] || C('--dim');
  row.innerHTML = `
    <span class="seg-dot" style="background:${{col}}"></span>
    <span class="seg-name">${{s.segment}}</span>
    <span class="seg-track">
      <span class="seg-fill" style="width:${{(s.revenue_share_pct/maxShare*100).toFixed(1)}}%;background:${{col}}"></span>
    </span>
    <span class="seg-pct">${{s.revenue_share_pct.toFixed(1)}}%</span>
  `;
  segBox.appendChild(row);
}});
</script>
</body>
</html>
"""

with open("outputs/dashboard.html", "w") as f:
    f.write(html)

print(f"dashboard.html written ({len(html):,} chars)")
