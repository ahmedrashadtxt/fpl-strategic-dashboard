import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace active_calc_gw parsing
old_active = '''        active_calc_gw = ongoing_gw if ongoing_gw else (last_finished_gw or next_gw_id)
        live_points_map = fetch_live_gameweek_points(active_calc_gw)
        squad_df["Raw_GW_Pts"] = squad_df["id"].map(lambda x: live_points_map.get(x, 0))
        squad_df["GW_Points"] = squad_df["Raw_GW_Pts"] * squad_df["Multiplier"]'''

new_active = '''        active_calc_gw = ongoing_gw if ongoing_gw else (last_finished_gw or next_gw_id)
        live_points_map = fetch_live_gameweek_points(active_calc_gw)
        squad_df["Raw_GW_Pts"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("total_points", 0))
        squad_df["Live_Mins"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("minutes", 0))
        squad_df["Live_Bonus"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("bonus", 0))
        squad_df["Live_BPS"] = squad_df["id"].map(lambda x: live_points_map.get(x, {}).get("bps", 0))
        squad_df["GW_Points"] = squad_df["Raw_GW_Pts"] * squad_df["Multiplier"]'''

text = text.replace(old_active, new_active)

# Replace eval_live_pts_map parsing
old_eval = '''            if selected_eval_gw != active_calc_gw:
                eval_live_pts_map = fetch_live_gameweek_points(selected_eval_gw)
                squad_df["Raw_GW_Pts"] = squad_df["id"].map(lambda x: eval_live_pts_map.get(x, 0))
                squad_df["GW_Points"] = squad_df["Raw_GW_Pts"] * squad_df["Multiplier"]'''

new_eval = '''            if selected_eval_gw != active_calc_gw:
                eval_live_pts_map = fetch_live_gameweek_points(selected_eval_gw)
                squad_df["Raw_GW_Pts"] = squad_df["id"].map(lambda x: eval_live_pts_map.get(x, {}).get("total_points", 0))
                squad_df["Live_Mins"] = squad_df["id"].map(lambda x: eval_live_pts_map.get(x, {}).get("minutes", 0))
                squad_df["Live_Bonus"] = squad_df["id"].map(lambda x: eval_live_pts_map.get(x, {}).get("bonus", 0))
                squad_df["Live_BPS"] = squad_df["id"].map(lambda x: eval_live_pts_map.get(x, {}).get("bps", 0))
                squad_df["GW_Points"] = squad_df["Raw_GW_Pts"] * squad_df["Multiplier"]'''

text = text.replace(old_eval, new_eval)

# Replace comp_live_pts_map parsing
old_comp = '''                comp_live_pts_map = fetch_live_gameweek_points(selected_eval_gw)
                comp_df["Raw_GW_Pts"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, 0))
                comp_df["GW_Points"] = comp_df["Raw_GW_Pts"] * comp_df["Multiplier"]'''

new_comp = '''                comp_live_pts_map = fetch_live_gameweek_points(selected_eval_gw)
                comp_df["Raw_GW_Pts"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("total_points", 0))
                comp_df["Live_Mins"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("minutes", 0))
                comp_df["Live_Bonus"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("bonus", 0))
                comp_df["Live_BPS"] = comp_df["id"].map(lambda x: comp_live_pts_map.get(x, {}).get("bps", 0))
                comp_df["GW_Points"] = comp_df["Raw_GW_Pts"] * comp_df["Multiplier"]'''

text = text.replace(old_comp, new_comp)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched squad_df_live")
