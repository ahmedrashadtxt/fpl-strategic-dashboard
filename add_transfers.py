import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add fetch_manager_transfers function
fetch_func = '''@st.cache_data(ttl=60, show_spinner=False)
def fetch_manager_transfers(manager_id: str):
    try:
        url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/transfers/"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

'''

# Insert it before fetch_manager_entry
text = text.replace('@st.cache_data(ttl=300, show_spinner=False)\ndef fetch_manager_entry', fetch_func + '@st.cache_data(ttl=300, show_spinner=False)\ndef fetch_manager_entry')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Added fetch_manager_transfers")
