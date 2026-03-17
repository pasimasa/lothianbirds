"""
GenerateReport.py
-----------------
Generates a formatted HTML report and writes it to report.html.
Intended to be run on a schedule via GitHub Actions.
"""

# ── Standard library imports ───────────────────────────────────────────────
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# ── Constants ─────────────────────────────────────────────────────────────
OUTPUT_FILE = "docs/index.html"
TIMEZONE = "Europe/London"
EBIRD_API_KEY_NAME = "EBIRD_API_KEY"
EBIRD_API_KEY = os.environ.get(EBIRD_API_KEY_NAME)
HEADERS = {'X-eBirdApiToken': EBIRD_API_KEY}
URL_BASE = 'https://ebird.org/ws2.0/data/obs/GB-SCT-ELN,GB-SCT-EDH,GB-SCT-MLN,GB-SCT-WLN/'
REGIONS = ['GB-SCT-ELN', 'GB-SCT-EDH', 'GB-SCT-MLN', 'GB-SCT-WLN']

# ── Functions ─────────────────────────────────────────────────────────────

def get_timestamp() -> str:
    """Return the current local time as a formatted string."""
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M")


def check_api_key() -> bool:
    """Return True if eBird API key is set and not empty."""
    return bool(os.environ.get(EBIRD_API_KEY_NAME))


def build_html(timestamp: str, checklists) -> str:
    # Build checklist bullet points
    checklist_items = "\n".join(
        f"<li><strong>{item[0]}</strong> — {item[1]} — {item[2]}</li>"
        for item in checklists
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


def get_last_n_days(n=6):
    """Generate list of dates for the last n days (including today) to use in API query"""
    today = datetime.now()
    dates = []
    for i in range(n):
        date = today - timedelta(days=i)
        dates.append(date.strftime("%Y/%m/%d"))
    return dates

def get_recent_checklists():
    """ Query eBird API to get list of recent checklists """
    dates = get_last_n_days(6)
    checklist_list = []
    for region in regions:
        for date in dates:
            url = f'https://api.ebird.org/v2/product/lists/' + region + '/' + date + '?maxResults=200'
            checklists = requests.get(url, headers=HEADERS).json()
            df = pd.DataFrame.from_records(checklists) 
            checklist_list.append(df)

    # Combine all checklists to one data frame
    df = pd.concat(checklist_list)

    # Convert isoObsDate to datetime
    df['isoObsDate'] = pd.to_datetime(df['isoObsDate'])

    # Remove checklist olders than 5 days (using time, not just date)
    cutoff_time = datetime.now() - timedelta(days=5)
    df = df[df['isoObsDate'] >= cutoff_time]

    checklists = df['subId'].unique()
    df.sort_values('isoObsDate', ascending=True, inplace=True)
    
    locations = []
    for index, row in df.iterrows():
        locName = row['loc']['locName']
        user = row['userDisplayName']
        obsDate = row['isoObsDate'].strftime('%d/%m/%Y %H:%M')
        locations.append([locName, user, obsDate])
        
    return locations


def write_report(html: str, output_file: str) -> None:
    """
    Write the HTML report to disk.

    Args:
        html:        The HTML content to write.
        output_file: The path of the file to write to.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point — orchestrates report generation."""
    print("Starting report generation...")

    start_time = time.time() # Record start time
    
    timestamp = get_timestamp()
    print(f"  Timestamp : {timestamp}")

    checklists = get_recent_checklists()
    
    html = build_html(timestamp, checklists)
    write_report(html, OUTPUT_FILE)
    print(f"  Output    : {OUTPUT_FILE}")

    print("Report generation complete.")


if __name__ == "__main__":
    main()
