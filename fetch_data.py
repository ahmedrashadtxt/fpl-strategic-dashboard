import requests
import sqlite3
import pandas as pd

# 1. Fetch Master Data (Players, Teams, Gameweeks)
bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
bootstrap_res = requests.get(bootstrap_url).json()

players_df = pd.DataFrame(bootstrap_res['elements'])
teams_df = pd.DataFrame(bootstrap_res['teams'])
positions_df = pd.DataFrame(bootstrap_res['element_types'])
events_df = pd.DataFrame(bootstrap_res['events'])

# 2. Fetch Full Season Fixtures
fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
fixtures_res = requests.get(fixtures_url).json()
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
conn = sqlite3.connect('fpl.db')
players_df.to_sql('players', conn, if_exists='replace', index=False)
teams_df.to_sql('teams', conn, if_exists='replace', index=False)
positions_df.to_sql('positions', conn, if_exists='replace', index=False)
events_df.to_sql('events', conn, if_exists='replace', index=False)
fixtures_df.to_sql('fixtures', conn, if_exists='replace', index=False)
conn.close()

print("Database successfully synced with players, fixtures, and events!")