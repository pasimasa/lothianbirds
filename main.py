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
from zoneinfo import ZoneInfo

import yaml

# ── Local imports ──────────────────────────────────────────────────────────
from html_generator import build_html

# ── Constants ─────────────────────────────────────────────────────────────
OUTPUT_FILE_ALL = "docs/birds_all.html"
OUTPUT_FILE_NOTABLE = "docs/index.html"
OBS_CACHE_FILE = "docs/obs_cache.csv"
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

def load_cached_obs(cache_file: str) -> pd.DataFrame:
    """Load cached observations, or return empty DataFrame if cache is stale or missing."""
    path = Path(cache_file)
    if not path.exists():
        return pd.DataFrame()
    
    cached = pd.read_csv(path)
    
    if cached.empty:
        return pd.DataFrame()

    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    obs_dates = pd.to_datetime(cached['obsDt']).dt.date
    if not (obs_dates == today).any():
        print("  Cache is from previous day, starting fresh.")
        return pd.DataFrame()

    return cached


def save_cached_obs(obs: pd.DataFrame, cache_file: str) -> None:
    """Persist observations to disk for reuse on next run."""
    Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
    obs.to_csv(cache_file, index=False)


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

    if not checklist_list:
        return []
        
    # Combine all checklists to one data frame
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

def get_species_config(yaml_file: str) -> dict:
    """
    Read species configuration details from yaml config file, return that as dictionary
    """
    with open(yaml_file, 'r', encoding='utf-8') as file:
        bird_config = yaml.safe_load(file) 

    return bird_config


def get_taxon_config(taxon_file: str) -> pd.DataFrame:
    """
    Read eBird taxon file and return as dataframe
    """
    return pd.read_csv(taxon_file)


def get_checklists_obs(checklists, cached_obs: pd.DataFrame) -> pd.DataFrame:
    """
    Query eBird API for checklist observations, skipping any subIds
    already present in cached_obs. Returns combined new + cached observations.
    """
    cached_ids = set()
    if not cached_obs.empty and 'subId' in cached_obs.columns:
        cached_ids = set(cached_obs['subId'].unique())

    new_obs = []
    for checklist in checklists:
        checklist_id = checklist[0]
        if checklist_id in cached_ids:
            continue  # already have this one

        try:
            url = f'https://api.ebird.org/v2/product/checklist/view/{checklist_id}'
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            sub = response.json()

            obs_df = pd.DataFrame.from_records(sub.get('obs'))
            if not obs_df.empty:
                obs_df['subId'] = checklist_id
                obs_df['locName'] = checklist[2]
                obs_df['obsDt'] = sub.get('obsDt')
                obs_df['userDisplayName'] = checklist[3]
                new_obs.append(obs_df)
        except (requests.RequestException, ValueError) as e:
            print(f"Error with checklist {checklist_id}: {e}")

    print(f"  Checklists: {len(checklists)} total, "
          f"{len(checklists) - len(new_obs)} cached, {len(new_obs)} fetched from API")

    if new_obs:
        new_df = pd.concat(new_obs, ignore_index=True)
        combined = pd.concat([cached_obs, new_df], ignore_index=True) if not cached_obs.empty else new_df
    else:
        combined = cached_obs.copy() if not cached_obs.empty else pd.DataFrame()

    # Keep only subIds still present in the current checklist window (prunes old data)
    current_ids = {c[0] for c in checklists}
    if not combined.empty:
        combined = combined[combined['subId'].isin(current_ids)]

    return combined


def update_obs_taxon(observations: pd.DataFrame, taxon: pd.DataFrame) -> pd.DataFrame:
    """
    Add taxon order, common and scientific names, convert sub-species to species
    and remove non-species records
    """
    # TODO
    # Convert sub-species codes to species code
    observations = observations.merge(taxon[['SPECIES_CODE', 'REPORT_AS']], left_on='speciesCode', right_on='SPECIES_CODE', how='left')
    observations['speciesCode'] = observations['REPORT_AS'].where(
        observations['REPORT_AS'].notna() & observations['REPORT_AS'].ne(''), observations['speciesCode'])
    observations = observations.drop(columns=['REPORT_AS'])

    # Add taxon order, common and scientific name and category (species or not), using taxon csv
    observations['taxon_order'] = observations['speciesCode'].map(taxon.set_index('SPECIES_CODE')['TAXON_ORDER'])
    observations['comName'] = observations['speciesCode'].map(taxon.set_index('SPECIES_CODE')['COMMON_NAME'])
    observations['sciName'] = observations['speciesCode'].map(taxon.set_index('SPECIES_CODE')['SCIENTIFIC_NAME'])
    observations['category'] = observations['speciesCode'].map(taxon.set_index('SPECIES_CODE')['CATEGORY'])

    # Keep only species records
    observations = observations[observations['category'] == 'species']
    
    # Drop category as not needed anymore
    observations = observations.drop('category', axis=1)
    
    return observations


def update_species_config(observations: pd.DataFrame, bird_config: dict) -> pd.DataFrame:
    """
    Populate new rarity field in obs
    Add minimum count for each
    """
    rare_map = {
        species: attrs.get("rarity", "common")
        for species, attrs in bird_config.items()
    }
    observations["rarity"] = observations["comName"].map(rare_map).fillna("normal")

    # Update species names using the yaml config
    name_map = {
        original_name: config["local_name"]
        for original_name, config in bird_config.items()
        if "local_name" in config
    }
    observations['comName'] = observations['comName'].replace(name_map)
    #    observations['comName'] = observations['comName'].replace(original_name, config['local_name'])
    return observations


def filter_notable_obs(obs: pd.DataFrame, bird_config: dict) -> pd.DataFrame:
    """
    Filter observations to notable ones only:
    - Remove records where count is 'X' (not counted)
    - Remove records where count is below the species min_count for the current month
    - Keep all records for species with no min_count in config
    """
    # Convert count to numeric, coerce X and other non-numeric to NaN
    obs = obs.copy()
    obs['count_numeric'] = pd.to_numeric(obs['howManyStr'], errors='coerce')
    obs = obs[obs['count_numeric'].notna()]

    current_month = datetime.now(ZoneInfo(TIMEZONE)).strftime('%b').lower()

    # Pre-build lookup: display name -> min count for this month
    min_count_lookup = {}
    for species, attrs in bird_config.items():
        display_name = attrs.get('local_name', species)
        min_count = attrs.get('min_count')
        if min_count is None:
            min_count_lookup[display_name] = 0
        elif isinstance(min_count, dict):
            min_count_lookup[display_name] = min_count.get(current_month, 0)
        else:
            min_count_lookup[display_name] = float(min_count)

    min_counts = obs['comName'].map(min_count_lookup).fillna(0)
    obs = obs[obs['count_numeric'] >= min_counts]

    return obs
    

# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point — orchestrates report generation."""
    print("Starting report generation...")

    if not EBIRD_API_KEY:
        print(f"Error: {EBIRD_API_KEY_NAME} environment variable not set")
        return

    start_time = time.time()
    timestamp = get_timestamp()
    print(f"  Timestamp : {timestamp}")

    species_config = get_species_config(CONFIG_YAML_FILE_NAME)
    taxon = get_taxon_config(TAXON_FILE_NAME)

    checklists = get_recent_checklists()

    # Load cache, fetch only new checklists, save updated cache
    cached_obs = load_cached_obs(OBS_CACHE_FILE)
    obs = get_checklists_obs(checklists, cached_obs)
    save_cached_obs(obs, OBS_CACHE_FILE)  # save before any filtering/processing

    obs = update_obs_taxon(obs, taxon)
    obs = update_species_config(obs, species_config)

    duration = time.time() - start_time
    print(f"  Checklists fetched in: {duration:.2f} seconds")

    html = build_html(timestamp, obs, duration)
    write_report(html, OUTPUT_FILE_ALL)
    print(f"  Output (all): {OUTPUT_FILE_ALL}")

    # Filter only for notable records
    obs_notable = filter_notable_obs(obs, species_config)
    
    html = build_html(timestamp, obs_notable, duration)
    write_report(html, OUTPUT_FILE_NOTABLE)
    print(f"  Output (notable): {OUTPUT_FILE_NOTABLE}")
    print("Report generation complete.")


if __name__ == "__main__":
    main()
