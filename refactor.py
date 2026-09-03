import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove find_all_chip_targets_cached
start_str = '@st.cache_data(ttl=900, show_spinner=False)\ndef find_all_chip_targets_cached'
end_str = 'def get_cached_league_eval_df'
if start_str in text and end_str in text:
    s_idx = text.find(start_str)
    e_idx = text.find(end_str)
    text = text[:s_idx] + text[e_idx:]
    print("Step 1 done")

# 2. Refactor the gameweek selector block
# From: if "tab4_simulated_chip" not in st.session_state:
# To: col_gw_sel, col_gw_ref = st.columns
start_str2 = '        if "tab4_simulated_chip" not in st.session_state:'
end_str2 = '        # -- Gameweek Selector & Refresh Row --'
if end_str2 not in text: # Might be corrupted characters
    end_str2 = '        col_gw_sel, col_gw_ref = st.columns([6.2, 0.8], vertical_alignment="center")'

if start_str2 in text and end_str2 in text:
    s_idx2 = text.find(start_str2)
    
    # Backtrack to the comment before col_gw_sel
    e_idx2 = text.find(end_str2)
    # find the previous #
    last_comment_idx = text.rfind('#', s_idx2, e_idx2)
    if last_comment_idx != -1:
        e_idx2 = last_comment_idx

    replacement2 = '''        all_gw_options = []
        if last_finished_gw is not None:
            all_gw_options.append(last_finished_gw)
        if ongoing_gw is not None:
            all_gw_options.append(ongoing_gw)
        all_gw_options.append(next_gw_id)
        all_gw_options = sorted(list(dict.fromkeys(all_gw_options)))

        def format_gw_label(g):
            if g in finished_gw_ids:
                return f"GW {g} (Finished)"
            elif g == ongoing_gw:
                return f"GW {g} (Live)"
            elif g == next_gw_id:
                return f"GW {g} (Upcoming)"
            else:
                return f"GW {g}"

        default_gw = ongoing_gw if ongoing_gw else next_gw_id

        if "tab4_selected_gw" not in st.session_state or st.session_state["tab4_selected_gw"] not in all_gw_options:
            st.session_state["tab4_selected_gw"] = default_gw

        default_idx = (
            all_gw_options.index(st.session_state["tab4_selected_gw"])
            if st.session_state["tab4_selected_gw"] in all_gw_options
            else 0
        )
        
        # Chip Selector for Upcoming GW
        active_chip = "None"
        if st.session_state["tab4_selected_gw"] == next_gw_id:
            active_chip = st.selectbox("Active Chip This GW:", ["None", "Triple Captain", "Bench Boost", "Free Hit"], key="tab4_active_chip")

'''
    text = text[:s_idx2] + replacement2 + text[e_idx2:]
    print("Step 2 done")

# 3. Refactor the cache and points logic
start_str3 = '            # -- Session-State Cache Key'
if start_str3 not in text:
    # Try different encoding
    start_str3 = '            state_key = ('
end_str3 = '            avg_xi_fdr = float(optimal_xi["FDR"].mean())'

if start_str3 in text and end_str3 in text:
    s_idx3 = text.find(start_str3)
    # backtrack if we missed the comment
    comment_idx = text.rfind('#', 0, s_idx3)
    if comment_idx != -1 and 'Session-State Cache Key' in text[comment_idx:s_idx3]:
        s_idx3 = comment_idx

    e_idx3 = text.find(end_str3)
    
    replacement3 = '''            # Session-State Cache Key: only recompute when relevant params change
            state_key = (
                f"squad_eval_{mgr_to_use}_{selected_eval_gw}_{enable_betting}"
                f"_{market_weight}_{factor_movement}_{active_chip}"
            )

            if state_key not in st.session_state:
                squad_eval_df = get_cached_league_eval_df(
                    conn, current_gw, selected_eval_gw, enable_betting, market_weight, factor_movement
                )
                try:
                    raw_opt_xi, raw_opt_bench, optimal_formation = solve_optimal_xi(squad_eval_df)
                except Exception as e:
                    st.error(f"Error solving optimal XI: {e}")
                    raw_opt_xi = squad_eval_df.head(11)
                    raw_opt_bench = squad_eval_df.tail(len(squad_eval_df) - 11)
                    optimal_formation = "Unknown"

                st.session_state[state_key] = {
                    "squad_eval_df": squad_eval_df,
                    "optimal_xi": raw_opt_xi,
                    "optimal_bench": raw_opt_bench,
                    "optimal_formation": optimal_formation,
                    "disagreements": sum(1 for p in raw_opt_xi.to_dict("records") if p.get("model_disagrees")),
                    "movements": sum(1 for p in raw_opt_xi.to_dict("records") if abs(p.get("market_move_pct", 0)) >= 3.0)
                }

            _cached = st.session_state[state_key]
            squad_eval_df = _cached["squad_eval_df"]
            optimal_xi = _cached["optimal_xi"].copy()
            optimal_bench = _cached["optimal_bench"].copy()
            optimal_formation = _cached["optimal_formation"]
            disagreements = _cached["disagreements"]
            movements = _cached["movements"]

            chip_active_on_gw = (active_chip != "None" and selected_eval_gw == next_gw_id)

            optimal_xi["is_cap"] = False
            optimal_xi["is_vc"] = False
            optimal_xi["Multiplier"] = 1
            if len(optimal_xi) > 0:
                top_id = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[0]["id"]
                optimal_xi.loc[optimal_xi["id"] == top_id, "is_cap"] = True
                optimal_xi.loc[optimal_xi["id"] == top_id, "Multiplier"] = 3 if (chip_active_on_gw and active_chip == "Triple Captain") else 2

            if len(optimal_xi) > 1:
                second_id = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[1]["id"]
                optimal_xi.loc[optimal_xi["id"] == second_id, "is_vc"] = True

            if not optimal_bench.empty:
                optimal_bench["is_cap"] = False
                optimal_bench["is_vc"] = False
                optimal_bench["Multiplier"] = 1
                if chip_active_on_gw and active_chip == "Bench Boost":
                    # Bench Boost active, multipliers remain 1 but they will be included in the total
                    pass

            # Calculate base points
            user_proj_xi_pts = optimal_xi["Proj_Pts"].sum()
            
            # Add normal captain double points (Proj_Pts only has 1x base points)
            if len(optimal_xi) > 0:
                cap_pts = optimal_xi.sort_values("Proj_Pts", ascending=False).iloc[0]["Proj_Pts"]
                user_proj_xi_pts += cap_pts  # Add once for 2x
                
                # Add again if Triple Captain
                if chip_active_on_gw and active_chip == "Triple Captain":
                    user_proj_xi_pts += cap_pts

            if chip_active_on_gw and active_chip == "Bench Boost":
                user_proj_xi_pts += optimal_bench["Proj_Pts"].sum()

'''
    text = text[:s_idx3] + replacement3 + text[e_idx3:]
    print("Step 3 done")

# 4. Replace other occurrences of simulated_chip with active_chip
text = text.replace('simulated_chip', 'active_chip')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
