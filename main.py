"""
GenerateReport.py
-----------------
Generates a formatted HTML report and writes it to report.html.
Intended to be run on a schedule via GitHub Actions.
"""

# ── Standard library imports ───────────────────────────────────────────────
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# ── Constants ─────────────────────────────────────────────────────────────
# This file must be configured in Actions workflow for commit
OUTPUT_FILE = "html/index.html" 
TIMEZONE = "Europe/London"

# ── Functions ─────────────────────────────────────────────────────────────

def get_timestamp() -> str:
    """Return the current local time as a formatted string."""
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M")

def check_api_key():
    """Return true if eBird API key found"""
    api_key = os.environ['EBIRD_API_KEY']
    if len(api_key) > 0:
        return true
    else:
        return false
    
def build_html(timestamp: str, msg) -> str:
    """
    Build and return the HTML report as a string.

    Args:
        timestamp: The timestamp to embed in the report.

    Returns:
        A complete HTML document as a string.
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
        <p>Generated {timestamp} - API test {msg}</p>
    </header>

    <div class="card">
        <h2>Report Status</h2>
        <p class="timestamp">Last updated: <strong>{timestamp}</strong></p>
    </div>

    <footer>
        Generated automatically by GitHub Actions
    </footer>
</body>
</html>"""


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

    msg = ''
    if check_api_key():
        msg =  'success'
    else:
        msg  =  'failed'
        
    timestamp = get_timestamp()
    print(f"  Timestamp : {timestamp}")

    html = build_html(timestamp,  msg)
    write_report(html, OUTPUT_FILE)
    print(f"  Output    : {OUTPUT_FILE}")

    print("Report generation complete.")


if __name__ == "__main__":
    main()
