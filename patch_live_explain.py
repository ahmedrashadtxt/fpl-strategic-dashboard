import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''        squad_df["Live_BPS"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("bps", 0))'''

new_logic = '''        squad_df["Live_BPS"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("bps", 0))
        squad_df["Live_Explain"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("explain", []))'''

text = text.replace(old_logic, new_logic)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched squad_df mapping")
