import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

filter_logic = '''
  # We will pick exactly 15 players.
  prob = pulp.LpProblem("FPL_Chip_Solver", pulp.LpMaximize)
  
  # Pre-filter candidate_league_df to valid players
  raw_avail = candidate_league_df[~candidate_league_df["id"].isin(blocked_in_set)].copy()
  
  # Dramatically reduce search space for PuLP to guarantee < 0.1s solve time
  top_cand_list = []
  for pos in ["GKP", "DEF", "MID", "FWD"]:
    pos_df = raw_avail[raw_avail["Pos"] == pos]
    if pos_df.empty:continue
    prem_cutoff = 8.5 if pos in ["MID", "FWD"] else 5.5
    mid_min = 6.5 if pos in ["MID", "FWD"] else 4.5
    prem_df = pos_df[pos_df["Cost"] >= prem_cutoff].sort_values(by="Horizon_xP", ascending=False).head(20)
    mid_df = pos_df[(pos_df["Cost"] >= mid_min) & (pos_df["Cost"] < prem_cutoff)].sort_values(by="Horizon_xP", ascending=False).head(25)
    bud_df = pos_df[pos_df["Cost"] < mid_min].sort_values(by="Horizon_xP", ascending=False).head(20)
    top_raw = pos_df.sort_values(by="Horizon_xP", ascending=False).head(30)
    top_cand_list.extend([prem_df, mid_df, bud_df, top_raw])
    
  # Always include current squad and targets to ensure a valid baseline path exists
  top_cand_list.append(raw_avail[raw_avail["id"].isin(current_squad_df["id"].tolist())])
  if target_in_set:
    top_cand_list.append(raw_avail[raw_avail["id"].isin(target_in_set)])
  if locked_set:
    top_cand_list.append(raw_avail[raw_avail["id"].isin(locked_set)])
    
  import pandas as pd
  avail = pd.concat(top_cand_list, ignore_index=True).drop_duplicates(subset=["id"])
'''

pattern = r'\s*# We will pick exactly 15 players\.\s*prob = pulp\.LpProblem\("FPL_Chip_Solver", pulp\.LpMaximize\)\s*# Pre-filter candidate_league_df to valid players\s*avail = candidate_league_df\[~candidate_league_df\["id"\]\.isin\(blocked_in_set\)\]\.copy\(\)'

text = re.sub(pattern, filter_logic, text)

# Also fix the budget text
budget_pattern = r'(\s*)st\.metric\("Available Budget", f"£\{team_val:\.1f\}m"\)'
budget_repl = r'''\1itb_val = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
\1squad_sell = round(team_val - itb_val, 1)
\1st.metric("Available Budget", f"£{team_val:.1f}m", help=f"Squad Sell Value:£{squad_sell:.1f}m | ITB:£{itb_val:.1f}m")
\1st.caption(f"Squad Sell Value:£{squad_sell:.1f}m | In The Bank:£{itb_val:.1f}m")'''

text = re.sub(budget_pattern, budget_repl, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Applied pulp optimization and budget display")
