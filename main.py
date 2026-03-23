"""
GenerateReport.py
-----------------
Generates a formatted HTML report and writes it to report.html.
Intended to be run on a schedule via GitHub Actions.
"""

# ── Standard library imports ───────────────────────────────────────────────
import os
import pandas as pd
import requests
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import yaml
from zoneinfo import ZoneInfo

# ── Local imports ──────────────────────────────────────────────────────────
from html_generator import build_html

# ── Constants ─────────────────────────────────────────────────────────────
OUTPUT_FILE = "docs/index.html"
TIMEZONE = "Europe/London"
EBIRD_API_KEY_NAME = "EBIRD_API_KEY"
EBIRD_API_KEY = os.environ.get(EBIRD_API_KEY_NAME)
HEADERS = {'X-eBirdApiToken': EBIRD_API_KEY}
REGIONS = ['GB-SCT-ELN', 'GB-SCT-EDH', 'GB-SCT-MLN', 'GB-SCT-WLN']
DAYS_TO_SHOW = 1 # using 1 for debugging, revert to 5 for production
CONFIG_YAML_FILE_NAME = "species_config.yml"
TAXON_FILE_NAME = "ebird_taxon.csv"

# ── Functions ─────────────────────────────────────────────────────────────

def get_timestamp() -> str:
    """Return the current local time as a formatted string."""
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M")


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
    dates = get_last_n_days(DAYS_TO_SHOW + 1) 
    checklist_list = []
    for region in REGIONS:
        for date in dates:
            url = f'https://api.ebird.org/v2/product/lists/{region}/{date}?maxResults=200'
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()  # Will raise an HTTPError for bad responses
                checklists = response.json()
            except (requests.RequestException, ValueError) as e:
                print(f"Error fetching data for {region} on {date}: {e}")
                continue
            df = pd.DataFrame.from_records(checklists) 
            checklist_list.append(df)

    # Combine all checklists to one data frame
    if not checklist_list:
        return []
    
    df = pd.concat(checklist_list, ignore_index=True)

    # Convert isoObsDate to timezone-aware UTC datetime
    df['isoObsDate'] = pd.to_datetime(df['isoObsDate'], utc=True)

    # Remove checklists older than 5 days (UTC)
    cutoff_time = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=DAYS_TO_SHOW)
    df = df[df['isoObsDate'] >= cutoff_time]

    if df.empty:
        return []

    df = df.sort_values('isoObsDate', ascending=True)
    
    df['locName'] = df['loc'].apply(lambda x: x['locName'])
    df['locID'] = df['loc'].apply(lambda x: x['locId'])
    df['obsDate'] = df['isoObsDate'].dt.strftime('%d/%m/%Y %H:%M')
    
    checklists = df[['subId', 'locID', 'locName', 'userDisplayName', 'obsDate']].values.tolist()

    return checklists

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

def get_species_config(yaml_file):
    """
    Read species configuration details from yaml config file, return that as dictionary
    """
    with open(os.path.join(yaml_file), 'r', encoding='utf-8') as file:
        bird_config = yaml.safe_load(file) 

    return bird_config


def get_taxon_config(taxon_file):
    """
    Read eBird taxon file and return as dataframe
    """
    return pd.read_csv(taxon_file)


def get_checklist_obs(checlists_list):
    """
    Query eBird API to get bird records for each checklist.
    Returns observations dataframe
    """
    for checklist_item in checklists_list:
        try:
            checklist = checklist_item[0]
            url = f'https://api.ebird.org/v2/product/checklist/view/{checklist}'
            sub = requests.get(url, headers=HEADERS).json()
            locId = sub.get('locId')
            
            userName = sub.get('userDisplayName')
            obsDate = sub.get('obsDt')
            
            obs_df = pd.DataFrame.from_records(sub.get('obs'))
            
            if not obs_df.empty: # ignore checklists with no species
                obs_df['subId'] = checklist
                obs_df['locName'] = checklist_item[2]
                obs_df['obsDt'] = obsDate
                obs_df['userName'] = userName
                obs.append(obs_df)
        except:
            print(f"Error with checklist {checklist}")

    if len(obs) > 0:
        observations = pd.concat(obs)
        return observations
    else:
        return []


def update_obs_taxon(obsservations, taxon):
    """
    Add taxon order, common and scientific names, convert sub-species to species
    """
    # TODO
    return 0
    

# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point — orchestrates report generation."""
    print("Starting report generation...")
    
    # Validate API key is available
    if not EBIRD_API_KEY:
        print(f"Error: {EBIRD_API_KEY_NAME} environment variable not set")
        return

    start_time = time.time() # Record start time
    
    timestamp = get_timestamp()
    print(f"  Timestamp : {timestamp}")

    checklists_start = time.time()

    # Read configs
    species_config = get_species_config(CONFIG_YAML_FILE_NAME)
    taxon = get_taxon_config(TAXON_FILE_NAME)
    
    checklists = get_recent_checklists()
    obs = get_cheklists_obs(checklists)

    obs = update_obs_taxon(obs, taxon)
    
    duration = time.time() - checklists_start
    print(f"  Checklists fetched in: {duration:.2f} seconds")
    
    html = build_html(timestamp, checklists, duration)
    write_report(html, OUTPUT_FILE)
    print(f"  Output    : {OUTPUT_FILE}")

    print("Report generation complete.")


if __name__ == "__main__":
    main()
