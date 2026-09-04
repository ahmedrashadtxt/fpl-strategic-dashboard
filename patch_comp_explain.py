import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''                comp_df["Live_BPS"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("bps", 0))'''

new_logic = '''                comp_df["Live_BPS"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("bps", 0))
                comp_df["Live_Explain"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("explain", []))'''

text = text.replace(old_logic, new_logic)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched comp_df mapping")
