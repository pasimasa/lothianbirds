# ── Standard library imports ───────────────────────────────────────────────
import html


def build_html(timestamp: str, checklists: list, duration: float) -> str:
    # Build checklist bullet points
    checklist_items = "\n".join(
        f"<li><strong>{html.escape(loc_name)}</strong> — {html.escape(user)} — {obs_date}</li>"
        for _, _, loc_name, user, obs_date in checklists # ignore first two values
    )
    checklist_html = f"<ul class='checklist'>{checklist_items}</ul>"
    
    # Calculate summary statistics
    num_checklists = len(checklists)
    unique_birders = len(set(user for _, _, _, user, _ in checklists))
    unique_locations = len(set(loc_id for _, loc_id, _, _, _ in checklists))
    
    # Build summary stats HTML
    summary_html = f"""
    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number">{num_checklists}</div>
            <div class="stat-label">Checklists</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{unique_locations}</div>
            <div class="stat-label">Locations</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{unique_birders}</div>
            <div class="stat-label">Birders</div>
        </div>
    </div>
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lothian Bird Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
            color: #333;
        }}
        header {{
            background: #4FA8D8;
            color: white;
            padding: 24px 32px;
            border-radius: 8px;
            margin-bottom: 24px;
        }}
        header h1 {{ margin: 0 0 4px; font-size: 28px; }}
        header p  {{ margin: 0; opacity: 0.8; font-size: 14px; }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 24px 32px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .card h2 {{ margin: 0 0 12px; font-size: 18px; color: #4FA8D8; }}
        .stats-container {{
            display: flex;
            gap: 24px;
            margin-bottom: 16px;
        }}
        .stat-box {{
            flex: 1;
            background: #E8F4F8;
            border-left: 4px solid #4FA8D8;
            padding: 16px;
            border-radius: 4px;
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            color: #4FA8D8;
            margin-bottom: 8px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        .timestamp {{ font-size: 14px; color: #666; }}
        .checklist {{
            list-style: disc;
            padding-left: 20px;
            margin: 0;
        }}
        .checklist li {{
            padding: 6px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
        }}
        .checklist li:last-child {{ border-bottom: none; }}
        footer {{
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 32px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Lothian recent bird sightings</h1>
        <p>Edinburgh, East Lothian, Midlothian, West Lothian</p>
    </header>
    <div class="card">
        <h2>Report Summary</h2>
        <p class="report-summary-subtitle">Notable eBird sightings from the past 5 days, including unverified records.</p>
        {summary_html}
        <p class="timestamp">Last updated: <strong>{timestamp}</strong></p>
    </div>
    <div class="card">
        <h2>Recent Checklists</h2>
        {checklist_html}
    </div>
    <footer>
        Generated automatically by GitHub Actions<br>
        Data fetching took {duration:.0f} seconds
    </footer>
</body>
</html>"""
