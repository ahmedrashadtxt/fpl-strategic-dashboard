import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_func = '''@st.cache_data(ttl=120, show_spinner=False)
def fetch_live_gameweek_points(eval_gw: int):
    try:
        live_url = f"https://fantasy.premierleague.com/api/event/{eval_gw}/live/"
        res = requests.get(live_url, timeout=10)
        if res.status_code == 200:
            return {
                item["id"]: item["stats"]["total_points"]
                for item in res.json().get("elements", [])
            }
        return {}
    except Exception:
        return {}'''

new_func = '''@st.cache_data(ttl=120, show_spinner=False)
def fetch_live_gameweek_points(eval_gw: int):
    try:
        live_url = f"https://fantasy.premierleague.com/api/event/{eval_gw}/live/"
        res = requests.get(live_url, timeout=10)
        if res.status_code == 200:
            return {
                item["id"]: {
                    "total_points": item["stats"]["total_points"],
                    "minutes": item["stats"]["minutes"],
                    "bonus": item["stats"]["bonus"],
                    "bps": item["stats"]["bps"]
                }
                for item in res.json().get("elements", [])
            }
        return {}
    except Exception:
        return {}'''

text = text.replace(old_func, new_func)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched fetch_live_gameweek_points")
