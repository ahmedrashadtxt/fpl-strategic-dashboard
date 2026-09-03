import sqlite3
import pandas as pd
import requests

conn = sqlite3.connect('fpl.db')
mgr_to_use = '7716321'
next_gw = 3

def fetch_transfer_manager_picks(manager_id: str, next_gw: int):
    try:
        url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{next_gw}/picks/"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        for g in range(next_gw - 1, 0, -1):
            res2 = requests.get(f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{g}/picks/", timeout=10)
            if res2.status_code == 200:
                return res2.json()
        return {}
    except Exception:
        return {}

picks_data = fetch_transfer_manager_picks(mgr_to_use, next_gw)
pick_ids = [p["element"] for p in picks_data.get("picks", [])]

print("pick_ids:", pick_ids)

if pick_ids:
    placeholders = ",".join(["?"] * len(pick_ids))
    cur = conn.cursor()
    cur.execute(f"SELECT SUM(now_cost) FROM players WHERE id IN ({placeholders})", pick_ids)
    res = cur.fetchone()[0]
    print("res:", res)
    squad_sell = round((res or 1000) / 10.0, 1)
    print("squad_sell:", squad_sell)

