import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

pulp_func = '''import pulp

def solve_chip_transfers_pulp(
  current_squad_df:pd.DataFrame,
  candidate_league_df:pd.DataFrame,
  team_value:float,
  locked_player_ids:list = None,
  target_in_player_ids:list = None,
  force_out_player_ids:list = None,
  blocked_in_player_ids:list = None,
) -> tuple[pd.DataFrame, list[dict]]:
  """Linear programming solver for 15-man squad overhaul (Wildcard/Free Hit)."""
  locked_set = set(locked_player_ids or [])
  blocked_in_set = set(blocked_in_player_ids or [])
  target_in_set = set(target_in_player_ids or []) - blocked_in_set
  
  # We will pick exactly 15 players.
  prob = pulp.LpProblem("FPL_Chip_Solver", pulp.LpMaximize)
  
  # Pre-filter candidate_league_df to valid players
  avail = candidate_league_df[~candidate_league_df["id"].isin(blocked_in_set)].copy()
  
  player_vars = {}
  starter_vars = {}
  
  for _, row in avail.iterrows():
    pid = row["id"]
    x = pulp.LpVariable(f"squad_{pid}", cat="Binary")
    y = pulp.LpVariable(f"start_{pid}", cat="Binary")
    player_vars[pid] = x
    starter_vars[pid] = y
    
    # Starter must be in squad
    prob += y <= x
    
    # Hard constraints
    if pid in locked_set or pid in target_in_set:
      prob += x == 1
    if pid in (force_out_player_ids or []) and pid not in locked_set:
      prob += x == 0
      
  # Position constraints for 15-man squad
  prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "GKP"]["id"]) == 2
  prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "DEF"]["id"]) == 5
  prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "MID"]["id"]) == 5
  prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "FWD"]["id"]) == 3
  prob += pulp.lpSum(player_vars.values()) == 15
  
  # Position constraints for 11-man starting XI
  prob += pulp.lpSum(starter_vars[pid] for pid in avail[avail["Pos"] == "GKP"]["id"]) == 1
  prob += pulp.lpSum(starter_vars[pid] for pid in avail[avail["Pos"] == "DEF"]["id"]) >= 3
  prob += pulp.lpSum(starter_vars[pid] for pid in avail[avail["Pos"] == "FWD"]["id"]) >= 1
  prob += pulp.lpSum(starter_vars.values()) == 11
  
  # Team constraints (max 3 per club)
  for team_id in avail["team_id"].unique():
    team_pids = avail[avail["team_id"] == team_id]["id"].tolist()
    prob += pulp.lpSum(player_vars[pid] for pid in team_pids) <= 3
    
  # Budget constraint
  prob += pulp.lpSum(player_vars[pid] * avail.loc[avail["id"]==pid, "Cost"].values[0] for pid in player_vars) <= team_value
  
  # Objective:Maximize starting XI points + 0.1 * bench points
  objective = pulp.lpSum(
    starter_vars[pid] * avail.loc[avail["id"]==pid, "Horizon_xP"].values[0] +
    0.1 * (player_vars[pid] - starter_vars[pid]) * avail.loc[avail["id"]==pid, "Horizon_xP"].values[0]
    for pid in player_vars
  )
  prob += objective
  
  prob.solve(pulp.PULP_CBC_CMD(msg=False))
  
  if pulp.LpStatus[prob.status] != 'Optimal':
    return current_squad_df.copy(), []
    
  selected_pids = [pid for pid in player_vars if pulp.value(player_vars[pid]) > 0.5]
  final_squad = avail[avail["id"].isin(selected_pids)].copy()
  
  final_squad["is_transfer_in"] = ~final_squad["id"].isin(current_squad_df["id"].tolist())
  final_squad["is_target_in"] = final_squad["id"].isin(target_in_set)
  
  # Mock paired transfers
  paired_transfers = []
  out_players = current_squad_df[~current_squad_df["id"].isin(selected_pids)].to_dict("records")
  in_players = final_squad[final_squad["is_transfer_in"]].to_dict("records")
  
  for p_out, p_in in zip(out_players, in_players):
    paired_transfers.append({
      "out":p_out,
      "in":p_in,
      "gain":round(p_in["Horizon_xP"] - p_out.get("Horizon_xP", 0), 1),
      "cost_diff":round(p_in["Cost"] - p_out.get("Cost", 0), 1),
      "target":p_in["id"] in target_in_set,
      "forced_out":p_out["id"] in (force_out_player_ids or []),
    })
    
  return final_squad, paired_transfers

'''

text = text.replace('def solve_multi_gw_transfers(', pulp_func + '\ndef solve_multi_gw_transfers(')

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("PuLP function added")
