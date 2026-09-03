import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_func = '''def solve_chip_transfers_pulp(
    current_squad_df: pd.DataFrame,
    candidate_league_df: pd.DataFrame,
    team_value: float,
    locked_player_ids: list = None,
    target_in_player_ids: list = None,
    force_out_player_ids: list = None,
    blocked_in_player_ids: list = None,
    is_free_hit: bool = False,
) -> tuple[pd.DataFrame, list[dict]]:
    """Linear programming solver for 15-man squad overhaul (Wildcard/Free Hit)."""
    import pulp
    locked_set = set(locked_player_ids or [])
    blocked_in_set = set(blocked_in_player_ids or [])
    target_in_set = set(target_in_player_ids or []) - blocked_in_set
    
    prob = pulp.LpProblem("FPL_Chip_Solver", pulp.LpMaximize)
    
    raw_avail = candidate_league_df[
        (~candidate_league_df["id"].isin(blocked_in_set)) &
        (candidate_league_df["Status"].isin(['a', 'd'])) &
        (candidate_league_df["Chance"] != 0) &
        (candidate_league_df["Chance"] != '0')
    ].copy()
    
    top_cand_list = []
    
    limits = {"GKP": 8, "DEF": 22, "MID": 25, "FWD": 16}
    for pos, limit in limits.items():
        pos_df = raw_avail[raw_avail["Pos"] == pos]
        if pos_df.empty: continue
        
        top_xp = pos_df.sort_values(by="Horizon_xP", ascending=False).head(limit)
        cheapest = pos_df.sort_values(by="Cost", ascending=True).head(4)
        
        top_cand_list.extend([top_xp, cheapest])
        
    current_in_raw = candidate_league_df[candidate_league_df["id"].isin(current_squad_df["id"].tolist())]
    top_cand_list.append(current_in_raw)
    
    if target_in_set:
        top_cand_list.append(candidate_league_df[candidate_league_df["id"].isin(target_in_set)])
    if locked_set:
        top_cand_list.append(candidate_league_df[candidate_league_df["id"].isin(locked_set)])
        
    import pandas as pd
    avail = pd.concat(top_cand_list, ignore_index=True).drop_duplicates(subset=["id"])
    
    player_vars = {}
    starter_vars = {}
    
    cost_dict = avail.set_index("id")["Cost"].to_dict()
    xp_dict = avail.set_index("id")["Horizon_xP"].to_dict()
    
    for pid in avail["id"]:
        x = pulp.LpVariable(f"squad_{pid}", cat="Binary")
        y = pulp.LpVariable(f"start_{pid}", cat="Binary")
        player_vars[pid] = x
        starter_vars[pid] = y
        
        prob += y <= x
        if pid in locked_set or pid in target_in_set:
            prob += x == 1
        if pid in (force_out_player_ids or []) and pid not in locked_set:
            prob += x == 0
            
    prob += pulp.lpSum(starter_vars[pid] for pid in avail[avail["Pos"] == "GKP"]["id"]) == 1
    prob += pulp.lpSum(starter_vars[pid] for pid in avail[avail["Pos"] == "DEF"]["id"]) >= 3
    prob += pulp.lpSum(starter_vars[pid] for pid in avail[avail["Pos"] == "FWD"]["id"]) >= 1
    prob += pulp.lpSum(starter_vars.values()) == 11
    
    prob += pulp.lpSum(
        starter_vars[pid] * xp_dict[pid] +
        0.10 * (player_vars[pid] - starter_vars[pid]) * xp_dict[pid]
        for pid in player_vars
    )

    prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "GKP"]["id"]) == 2
    prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "DEF"]["id"]) == 5
    prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "MID"]["id"]) == 5
    prob += pulp.lpSum(player_vars[pid] for pid in avail[avail["Pos"] == "FWD"]["id"]) == 3
    prob += pulp.lpSum(player_vars.values()) == 15
    
    for team_id in avail["team_id"].unique():
        team_pids = avail[avail["team_id"] == team_id]["id"].tolist()
        prob += pulp.lpSum(player_vars[pid] for pid in team_pids) <= 3
        
    prob += pulp.lpSum(player_vars[pid] * cost_dict[pid] for pid in player_vars) <= team_value
    
    prob.solve(pulp.PULP_CBC_CMD(timeLimit=6, gapRel=0.01, msg=False))
    
    if pulp.LpStatus[prob.status] != 'Optimal':
        return current_squad_df.copy(), []
        
    selected_pids = [pid for pid in player_vars if pulp.value(player_vars[pid]) > 0.5]
    final_squad = avail[avail["id"].isin(selected_pids)].copy()
    
    final_squad["is_transfer_in"] = ~final_squad["id"].isin(current_squad_df["id"].tolist())
    final_squad["is_target_in"] = final_squad["id"].isin(target_in_set)
    
    paired_transfers = []
    out_players = current_squad_df[~current_squad_df["id"].isin(selected_pids)].to_dict("records")
    in_players = final_squad[final_squad["is_transfer_in"]].to_dict("records")
    
    # Position-matched swaps
    matched_in_indices = set()
    for p_out in list(out_players):
        for i, p_in in enumerate(in_players):
            if i not in matched_in_indices and p_in["Pos"] == p_out["Pos"]:
                matched_in_indices.add(i)
                paired_transfers.append({
                    "out": p_out,
                    "in": p_in,
                    "gain": round(p_in["Horizon_xP"] - p_out.get("Horizon_xP", 0), 1),
                    "cost_diff": round(p_in["Cost"] - p_out.get("Cost", 0), 1),
                    "target": p_in["id"] in target_in_set,
                    "forced_out": p_out["id"] in (force_out_player_ids or []),
                })
                out_players.remove(p_out)
                break

    # Leftovers
    leftover_in = [p for i, p in enumerate(in_players) if i not in matched_in_indices]
    for p_out, p_in in zip(out_players, leftover_in):
        paired_transfers.append({
            "out": p_out,
            "in": p_in,
            "gain": round(p_in["Horizon_xP"] - p_out.get("Horizon_xP", 0), 1),
            "cost_diff": round(p_in["Cost"] - p_out.get("Cost", 0), 1),
            "target": p_in["id"] in target_in_set,
            "forced_out": p_out["id"] in (force_out_player_ids or []),
        })
        
    return final_squad, paired_transfers'''

pattern = r'def solve_chip_transfers_pulp\(.*?\)\s*->\s*tuple\[pd\.DataFrame,\s*list\[dict\]\]:.*?return final_squad,\s*paired_transfers'
text = re.sub(pattern, new_func, text, flags=re.DOTALL)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated solve_chip_transfers_pulp")
