import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

start_pattern = r'(\s*)chip_active_on_gw = \(active_chip != "None"\)'
end_pattern = r'(\s*)avg_xi_fdr = float\(optimal_xi\["FDR"\]\.mean\(\)\)'

match_start = re.search(start_pattern, text)
match_end = re.search(end_pattern, text)

if match_start and match_end:
  indent = match_start.group(1)
  replacement = f'''{indent}chip_active_on_gw = (active_chip != "None" and selected_eval_gw == next_gw_id)

{indent}# Strictly enforce 1 Captain and 1 Vice Captain
{indent}optimal_xi["is_cap"] = False
{indent}optimal_xi["is_vc"] = False
{indent}optimal_xi["Multiplier"] = 1
{indent}if not optimal_bench.empty:
{indent}  optimal_bench["is_cap"] = False
{indent}  optimal_bench["is_vc"] = False
{indent}  optimal_bench["Multiplier"] = 1

{indent}if len(optimal_xi) > 0:
{indent}  top_id = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[0]["id"]
{indent}  optimal_xi.loc[optimal_xi["id"] == top_id, "is_cap"] = True
{indent}  optimal_xi.loc[optimal_xi["id"] == top_id, "Multiplier"] = 3 if (chip_active_on_gw and active_chip == "Triple Captain") else 2

{indent}if len(optimal_xi) > 1:
{indent}  second_id = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[1]["id"]
{indent}  optimal_xi.loc[optimal_xi["id"] == second_id, "is_vc"] = True

{indent}# Calculate base points
{indent}user_proj_xi_pts = optimal_xi["Proj_Pts"].sum()
{indent}
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
  new_text = text[:match_start.start()] + replacement + text[match_end.start():]
  
  # Also clean up the chip_note logic since target_chip_gw is gone
  chip_note_pattern = r'(\s*)if chip_active_on_gw:.*?else:\s*chip_note = ""'
  new_text = re.sub(chip_note_pattern, r'\1chip_note = f" &bull; <span style=\'color:#eab308;\'>Active Simulation:{active_chip}</span>" if chip_active_on_gw else ""', new_text, flags=re.DOTALL)
  
  with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(new_text)
  print("Fixed scoring and chip notes successfully!")
else:
  print("Could not find start/end markers")
