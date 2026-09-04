import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Dream Team name
old_dt = '''        return {
            "type": "dream_team",
            "manager_name": "Super Team",
            "player_name": "Official Dream Team",'''
            
new_dt = '''        return {
            "type": "dream_team",
            "manager_name": "Team of the Week",
            "player_name": "Official Dream Team",'''

text = text.replace(old_dt, new_dt)

# 2. Update MOTW to fallback to World #1 Manager
pattern = re.compile(r"def fetch_motw_manager_data\(target_gw: int\):.*?return \{(.*?)\}", re.DOTALL)

new_motw = '''def fetch_motw_manager_data(target_gw: int):
    motw_id = None
    motw_score = None
    fallback_used = False
    try:
        bs_res = requests.get(
            "https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10
        )
        if bs_res.status_code == 200:
            bs_events = bs_res.json().get("events", [])
            for ev in bs_events:
                if ev.get("id") == target_gw:
                    motw_id = ev.get("highest_scoring_entry")
                    motw_score = ev.get("highest_score")
                    break
    except Exception:
        pass

    if not motw_id:
        try:
            league_res = requests.get("https://fantasy.premierleague.com/api/leagues-classic/314/standings/", timeout=10)
            if league_res.status_code == 200:
                results = league_res.json().get("standings", {}).get("results", [])
                if results:
                    motw_id = results[0].get("entry")
                    motw_score = results[0].get("event_total")
                    fallback_used = True
        except Exception:
            pass

    if motw_id:
        try:
            mgr_info = requests.get(
                f"https://fantasy.premierleague.com/api/entry/{motw_id}/", timeout=10
            ).json()
            mgr_name = mgr_info.get("name", "World #1 Manager" if fallback_used else "Top Manager")
            player_name = (
                f"{mgr_info.get('player_first_name', '')}"
                f" {mgr_info.get('player_last_name', '')}".strip()
            )
            picks_res = requests.get(
                f"https://fantasy.premierleague.com/api/entry/{motw_id}/event/{target_gw}/picks/",
                timeout=10,
            ).json()
            picks_list = picks_res.get("picks", [])
            
            final_score = motw_score or picks_res.get("entry_history", {}).get("points", 0)
            
            return {
                "type": "motw",
                "manager_name": mgr_name,
                "player_name": player_name,
                "total_score": final_score,
                "picks": picks_list,
            }'''

text = pattern.sub(new_motw, text)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched MOTW logic")
