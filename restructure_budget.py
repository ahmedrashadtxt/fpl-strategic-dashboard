import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Move squad_df query up.
# Find the line where pick_ids is checked
pattern_insert = r'(pick_ids = \[p\["element"\] for p in picks_data\.get\("picks", \[\]\)\]\n\s*if not pick_ids:\n\s*st\.warning\("No squad picks retrieved for this manager\."\)\n\s*return\n)'

squad_df_logic = '''
    placeholders = ",".join(["?"] * len(pick_ids))
    squad_query = f"""
    SELECT p.id, p.code, p.photo, p.web_name AS Player, p.team AS team_id,
           t.short_name AS Team,
           CASE p.element_type WHEN 1 THEN 'GKP' WHEN 2 THEN 'DEF' WHEN 3 THEN 'MID' WHEN 4 THEN 'FWD' END AS Pos,
           p.now_cost / 10.0 AS Cost, p.minutes AS minutes,
           p.total_points AS Season_Points, p.form AS Form, p.points_per_game AS PPG,
           p.status AS Status, p.chance_of_playing_next_round AS Chance, p.news AS News
    FROM players p
    INNER JOIN teams t ON p.team = t.id
    WHERE p.id IN ({placeholders})
    """
    import pandas as pd
    squad_df = pd.read_sql(squad_query, conn, params=pick_ids)
'''
text = re.sub(pattern_insert, r'\1' + squad_df_logic, text)

# 2. Remove the old squad_df logic further down
pattern_remove = r'\s*placeholders = ","\.join\(\["\?"\] \* len\(pick_ids\)\)\n\s*squad_query = f"""\n\s*SELECT p\.id.*?WHERE p\.id IN \(\{placeholders\}\)\n\s*"""\n\s*squad_df = pd\.read_sql\(squad_query, conn, params=pick_ids\)'
text = re.sub(pattern_remove, '', text, flags=re.DOTALL)

# 3. Update the budget calculation before chip_mode
budget_calc_pattern = r'\s*if pick_ids:.*?team_val = round\(squad_sell \+ itb_val, 1\)'
budget_calc_repl = '''
    itb_val = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
    squad_sell = round(squad_df["Cost"].sum(), 1) if not squad_df.empty else 100.0
    team_val = round(squad_sell + itb_val, 1)'''
text = re.sub(budget_calc_pattern, budget_calc_repl, text, flags=re.DOTALL)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Restructured squad_df and budget")
