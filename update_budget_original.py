import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Insert squad_df logic right after pick_ids checking
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

    # Calculate Budget dynamically
    itb_val = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
    squad_sell = round(squad_df["Cost"].sum(), 1) if not squad_df.empty else 100.0
    team_val = round(squad_sell + itb_val, 1)
'''
text = re.sub(pattern_insert, r'\1' + squad_df_logic, text)

# 2. Delete the old squad_df query
pattern_remove_squad = r'\s*placeholders = ","\.join\(\["\?"\] \* len\(pick_ids\)\)\n\s*squad_query = f"""\n\s*SELECT p\.id.*?WHERE p\.id IN \(\{placeholders\}\)\n\s*"""\n\s*squad_df = pd\.read_sql\(squad_query, conn, params=pick_ids\)'
text = re.sub(pattern_remove_squad, '', text, flags=re.DOTALL)

# 3. Fix the budget in the UI blocks
# In the original file, it has:
# team_val = entry_hist.get("value", mgr_data.get("last_deadline_value", 1000)) / 10.0
# itb_val = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
# squad_sell = round(team_val - itb_val, 1)
# We will just remove these lines since they are defined globally now!
pattern_remove_budget = r'\s*team_val = entry_hist\.get\("value", mgr_data\.get\("last_deadline_value", 1000\)\) / 10\.0\n\s*itb_val = entry_hist\.get\("bank", mgr_data\.get\("last_deadline_bank", 0\)\) / 10\.0\n\s*squad_sell = round\(team_val - itb_val, 1\)'
text = re.sub(pattern_remove_budget, '', text)

# Wait! The original might have some lines separated. Let's just blindly replace them.
text = re.sub(r'\s*team_val = entry_hist\.get\("value".*? / 10\.0', '', text)
text = re.sub(r'\s*itb_val = entry_hist\.get\("bank".*? / 10\.0', '', text)
text = re.sub(r'\s*squad_sell = round\(team_val - itb_val, 1\)', '', text)

# Ensure the UI metric renders the new variables correctly!
# Replace st.metric("Available Budget", f"£{team_val:.1f}m")
# The original file has: st.metric("Available Budget", f"£{team_val:.1f}m")
# We will append the caption below it.
metric_pattern = r'(st\.metric\("Available Budget", f"£\{team_val:\.1f\}m"\))'
metric_repl = r'''\1
        st.caption(f"Squad Sell Value: £{squad_sell:.1f}m | In The Bank: £{itb_val:.1f}m")'''
text = re.sub(metric_pattern, metric_repl, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated budget successfully")
