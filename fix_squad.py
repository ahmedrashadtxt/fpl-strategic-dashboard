import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  content = f.read()

# Replace the block from state_key to avg_xi_fdr
start_pattern = r'(\s*)# -- Session-State Cache Key'
if not re.search(start_pattern, content):
  start_pattern = r'(\s*)state_key = \('

end_pattern = r'(\s*)avg_xi_fdr = float\(optimal_xi\["FDR"\]\.mean\(\)\)'

match_start = re.search(start_pattern, content)
match_end = re.search(end_pattern, content)

if match_start and match_end:
  start_idx = match_start.start()
  end_idx = match_end.start()
  
  indent = match_start.group(1)
  
  replacement = f'''{indent}# Session-State Cache Key:only recompute when relevant params change
{indent}state_key = (
{indent}  f"squad_eval_{{mgr_to_use}}_{{selected_eval_gw}}_{{enable_betting}}"
{indent}  f"_{{market_weight}}_{{factor_movement}}_{{active_chip}}"
{indent})

{indent}if state_key not in st.session_state:
{indent}  squad_eval_df = get_cached_league_eval_df(
{indent}    conn, current_gw, selected_eval_gw, enable_betting, market_weight, factor_movement
{indent}  )
{indent}  try:
{indent}    raw_opt_xi, raw_opt_bench, optimal_formation = solve_optimal_xi(squad_eval_df)
{indent}  except Exception as e:
{indent}    st.error(f"Error solving optimal XI:{{e}}")
{indent}    raw_opt_xi = squad_eval_df.head(11)
{indent}    raw_opt_bench = squad_eval_df.tail(len(squad_eval_df) - 11)
{indent}    optimal_formation = "Unknown"

{indent}  st.session_state[state_key] = {{
{indent}    "squad_eval_df":squad_eval_df,
{indent}    "optimal_xi":raw_opt_xi,
{indent}    "optimal_bench":raw_opt_bench,
{indent}    "optimal_formation":optimal_formation,
{indent}    "disagreements":sum(1 for p in raw_opt_xi.to_dict("records") if p.get("model_disagrees")),
{indent}    "movements":sum(1 for p in raw_opt_xi.to_dict("records") if abs(p.get("market_move_pct", 0)) >= 3.0)
{indent}  }}

{indent}_cached = st.session_state[state_key]
{indent}squad_eval_df = _cached["squad_eval_df"]
{indent}optimal_xi = _cached["optimal_xi"].copy()
{indent}optimal_bench = _cached["optimal_bench"].copy()
{indent}optimal_formation = _cached["optimal_formation"]
{indent}disagreements = _cached["disagreements"]
{indent}movements = _cached["movements"]

{indent}chip_active_on_gw = (active_chip != "None" and selected_eval_gw == next_gw_id)

{indent}optimal_xi["is_cap"] = False
{indent}optimal_xi["is_vc"] = False
{indent}optimal_xi["Multiplier"] = 1
{indent}if len(optimal_xi) > 0:
{indent}  top_id = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[0]["id"]
{indent}  optimal_xi.loc[optimal_xi["id"] == top_id, "is_cap"] = True
{indent}  optimal_xi.loc[optimal_xi["id"] == top_id, "Multiplier"] = 3 if (chip_active_on_gw and active_chip == "Triple Captain") else 2

{indent}if len(optimal_xi) > 1:
{indent}  second_id = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[1]["id"]
{indent}  optimal_xi.loc[optimal_xi["id"] == second_id, "is_vc"] = True

{indent}if not optimal_bench.empty:
{indent}  optimal_bench["is_cap"] = False
{indent}  optimal_bench["is_vc"] = False
{indent}  optimal_bench["Multiplier"] = 1

{indent}# Calculate base points
{indent}user_proj_xi_pts = optimal_xi["Proj_Pts"].sum()

{indent}# Add normal captain double points (Proj_Pts only has 1x base points)
{indent}if len(optimal_xi) > 0:
{indent}  cap_pts = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[0]["Proj_Pts"]
{indent}  user_proj_xi_pts += cap_pts # Add once for 2x
{indent}  
{indent}  # Add again if Triple Captain
{indent}  if chip_active_on_gw and active_chip == "Triple Captain":
{indent}    user_proj_xi_pts += cap_pts

{indent}if chip_active_on_gw and active_chip == "Bench Boost":
{indent}  user_proj_xi_pts += optimal_bench["Proj_Pts"].sum()

'''
  
  new_content = content[:start_idx] + replacement + content[end_idx:]
  with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
  print("Replaced logic chunk successfully!")
else:
  print("Could not find bounds")
