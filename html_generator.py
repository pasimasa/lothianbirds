# ── Standard library imports ───────────────────────────────────────────────
import datetime
import html
import pandas as pd

RARITY_COLOURS = {
    "rare":   "#cc0000",
    "medium": "#cc6600",
    "normal": "#000000",
}


def build_html(timestamp: str, obs_df: pd.DataFrame, duration: float) -> str:
    """
    Generate html report using data in input data frame

    Return html string that can be written to file
    """
    # --- Stats (using checklist/location/user level, not obs level) ---
    num_checklists = obs_df["subId"].nunique()
    unique_locations = obs_df["locName"].nunique()
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
            <div class="stat-label">Total records</div>
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

    # --- Observations grouped by species, sorted by taxon_order then date ---
    obs_df = obs_df.copy()
    obs_df["obsDt"] = pd.to_datetime(obs_df["obsDt"])

    has_comments = "comments" in obs_df.columns
    if not has_comments:
        print("Warning: 'comments' column not found in data — observation comments will be omitted from the report.")

    species_sections = []
    # Sort species by taxon_order (take the first value per species as it's constant)
    grouped_by_species = obs_df.groupby("speciesCode")
    species_order = (
        grouped_by_species["taxon_order"]
        .first()
        .sort_values()
        .index
    )

    for species_code in species_order:
        group = grouped_by_species.get_group(species_code)
        group_sorted = group.sort_values("obsDt", ascending=False)

        # Get display names from first row (same for all rows in group)
        first = group_sorted.iloc[0]
        com_name = html.escape(first["comName"])
        sci_name = html.escape(first["sciName"])
        rarity = first.get("rarity", "normal")
        name_colour = RARITY_COLOURS.get(rarity, "#000000")

        row_html_parts = []
        for row in group_sorted.itertuples():
            comment_html = ""
            if has_comments:
                val = getattr(row, "comments", None)
                if pd.notna(val) and str(val).strip():
                    escaped_comment = html.escape(str(val))
                    comment_html = f' <span class="obs-comment">"{escaped_comment}"</span>'
            row_html_parts.append(f"""<li>
                {row.obsDt.strftime('%d/%m/%y')} {html.escape(row.locName)} <strong>{html.escape(str(row.howManyStr))}</strong> ({html.escape(row.userDisplayName)}){comment_html}</li>""")
        rows = "\n".join(row_html_parts)
        
        species_sections.append(f"""
            <div class="species-block">
                <h4 class="species-name" style="color: {name_colour};">{com_name} <span class="sci-name">({sci_name})</span></h4>
                <ul class="observation">{rows}</ul>
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
            padding: 10px 14px;
            border-radius: 4px;
        }}
        .stat-number {{
            font-size: 22px;
            font-weight: bold;
            color: #4FA8D8;
            margin-bottom: 8px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        .timestamp {{ font-size: 14px; color: #666; }}
        .observation {{
            list-style: disc;
            padding-left: 20px;
            margin: 0;
        }}
        .species-name {{
            font-size: 14px;
            font-weight: 600;
            margin: 16px 0 2px 0;
            padding-bottom: 0px;
        }}
        .sci-name {{
            font-style: italic;
            font-weight: normal;
            color: #666;
            font-size: 13px;
        }}
        .observation li {{
            padding: 6px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
        }}
        .report-summary-subtitle {{
            margin: -8px 0 16px;
            font-size: 14px;
            color: #888;
        }}
        .obs-comment {{
            color: #999;
            font-style: italic;
            font-size: 13px;
        }}
        .observation li:last-child {{ border-bottom: none; }}
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
