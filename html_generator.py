# ── Standard library imports ───────────────────────────────────────────────
import datetime
import html


def build_html(timestamp: str, obs_df: pd.DataFrame, duration: float) -> str:
    # --- Stats (using checklist/location/user level, not obs level) ---
    num_checklists = obs_df["subId"].nunique()
    unique_locations = obs_df["locId"].nunique()
    unique_birders = obs_df["userDisplayName"].nunique()
    num_observations = len(obs_df)

    summary_html = f"""
    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number">{num_checklists}</div>
            <div class="stat-label">Checklists</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{num_observations}</div>
            <div class="stat-label">Observations</div>
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

    # --- Observations grouped by species, sorted by date within each ---
    obs_df = obs_df.copy()
    obs_df["obsDt"] = pd.to_datetime(obs_df["obsDt"])

    species_sections = []
    for species_code, group in obs_df.groupby("speciesCode"):
        group_sorted = group.sort_values("obsDt", ascending=False)
        rows = "\n".join(
            f"""<li>
                <strong>{html.escape(str(row['howManyStr']))}</strong>
                — {html.escape(row['userDisplayName'])}
                — {row['obsDt'].strftime('%d %b %Y %H:%M')}
            </li>"""
            for _, row in group_sorted.iterrows()
        )
        species_sections.append(f"""
            <div class="species-block">
                <h3>{html.escape(species_code)}</h3>
                <ul class="checklist">{rows}</ul>
            </div>
        """)

    observations_html = "\n".join(species_sections)
    accessed_date = datetime.date.today().strftime("%B %d, %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lothian Bird Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1400px;
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
        .report-summary-subtitle {{
            margin: -8px 0 16px;
            font-size: 14px;
            color: #888;
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
        <h2>Recent Sightings</h2>
        {observations_html}
    </div>
    <footer>
        eBird. 2021. eBird: An online database of bird distribution and abundance [web application]. eBird, Cornell Lab of Ornnithology, Ithaca, New York. Available: http://www.ebird.org. (Accessed: {accessed_date}).<br><br>
        Generated automatically by GitHub Actions<br>
        Data fetching took {duration:.0f} seconds
    </footer>
</body>
</html>"""
