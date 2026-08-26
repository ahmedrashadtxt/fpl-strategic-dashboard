import requests
import sqlite3
import pandas as pd
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def fetch_data():
    """
    Fetches master data and fixtures from the official Premier League/FPL API
    and saves them into the SQLite database.
    """
    # Configure retry strategy
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://fantasy.premierleague.com/",
        "Origin": "https://fantasy.premierleague.com"
    }

    # Helper function to get JSON with logging and validation
    def get_json(url):
        print(f"Fetching from: {url}")
        try:
            response = session.get(url, headers=headers, timeout=20)
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}", file=sys.stderr)
                print(f"Response Headers: {response.headers}", file=sys.stderr)
                print(f"Response Preview: {response.text[:1000]}", file=sys.stderr)
                response.raise_for_status()
                
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred for {url}: {http_err}", file=sys.stderr)
            raise
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"JSON decode error for {url}: {json_err}", file=sys.stderr)
            if 'response' in locals() and response is not None:
                print(f"Response Content (first 1000 chars):\n{response.text[:1000]}", file=sys.stderr)
            raise
        except Exception as err:
            print(f"An unexpected error occurred for {url}: {err}", file=sys.stderr)
            raise

    # 1. Fetch Master Data (Players, Teams, Gameweeks)
    bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    bootstrap_res = get_json(bootstrap_url)

    print("Master data successfully retrieved. Processing dataframes...")
    players_df = pd.DataFrame(bootstrap_res['elements'])
    teams_df = pd.DataFrame(bootstrap_res['teams'])
    positions_df = pd.DataFrame(bootstrap_res['element_types'])
    events_df = pd.DataFrame(bootstrap_res['events'])

    # 2. Fetch Full Season Fixtures
    fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
    fixtures_res = get_json(fixtures_url)
    print("Fixtures data successfully retrieved. Processing dataframe...")
    fixtures_df = pd.DataFrame(fixtures_res)

    # 3. Clean and sanitize object types for SQLite
    def clean_lists(df):
        return df.map(lambda x: str(x) if isinstance(x, (list, dict)) else x)

    players_df = clean_lists(players_df)
    teams_df = clean_lists(teams_df)
    positions_df = clean_lists(positions_df)
    events_df = clean_lists(events_df)
    fixtures_df = clean_lists(fixtures_df)

    # 4. Save into SQLite
    print("Writing data to fpl.db...")
    conn = sqlite3.connect('fpl.db')
    try:
        players_df.to_sql('players', conn, if_exists='replace', index=False)
        teams_df.to_sql('teams', conn, if_exists='replace', index=False)
        positions_df.to_sql('positions', conn, if_exists='replace', index=False)
        events_df.to_sql('events', conn, if_exists='replace', index=False)
        fixtures_df.to_sql('fixtures', conn, if_exists='replace', index=False)
        print("Database successfully synced with players, fixtures, and events!")
    finally:
        conn.close()

def fetch_all_data():
    """Compatibility wrapper for fetch_data()"""
    fetch_data()

def main():
    """Compatibility wrapper for fetch_data()"""
    fetch_data()

if __name__ == "__main__":
    fetch_data()
