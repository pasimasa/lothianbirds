def build_html(timestamp: str, checklists: list) -> str:
    # Build checklist bullet points
    checklist_items = "\n".join(
        f"<li><strong>{loc_name}</strong> — {user} — {obs_date}</li>"
        for loc_name, user, obs_date in checklists
    )
    checklist_html = f"<ul class='checklist'>{checklist_items}</ul>"

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
            background: #2c6e49;
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
        .card h2 {{ margin: 0 0 12px; font-size: 18px; color: #2c6e49; }}
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
        <p>Generated {timestamp}</p>
    </header>
    <div class="card">
        <h2>Report Status</h2>
        <p class="timestamp">Last updated: <strong>{timestamp}</strong></p>
    </div>
    <div class="card">
        <h2>Recent Checklists</h2>
        {checklist_html}
    </div>
    <footer>
        Generated automatically by GitHub Actions
    </footer>
</body>
</html>"""