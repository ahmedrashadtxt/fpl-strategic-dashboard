import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

target_str = '''                unsafe_allow_html=True,
            )

            if enable_comparison and comp_data:
                col_left, col_right = st.columns(2)'''

new_str = '''                unsafe_allow_html=True,
            )
            
            # Compute formation
            defs = len(user_starters[user_starters["Pos"] == "DEF"])
            mids = len(user_starters[user_starters["Pos"] == "MID"])
            fwds = len(user_starters[user_starters["Pos"] == "FWD"])
            user_formation = f"{defs}-{mids}-{fwds}"
            
            pts_delta_str = f"{pts_diff:+d} vs Comp" if enable_comparison and comp_data else None
            pts_label = "Current Points (Live)" if is_ongoing_gw else "Total Points (Finished)"
            
            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
            col_met1.metric("Squad Formation", user_formation)
            col_met2.metric(pts_label, f"{user_eval_pts} pts", delta=pts_delta_str)
            col_met3.metric("Manager Transfers", f"{transfers_cost // 4} made")
            col_met4.metric(
                "Squad Health",
                f"{len(squad_df[squad_df['Status'] == 'a'])}/15 Fit",
                delta="Available" if len(squad_df[squad_df['Status'] != 'a']) == 0 else "Flagged",
            )
            
            if enable_comparison and comp_data:
                col_left, col_right = st.columns(2)'''

text = text.replace(target_str, new_str)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched live metric box")
