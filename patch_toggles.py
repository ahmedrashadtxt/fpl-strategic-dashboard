import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to replace the toggle block from col_tgl1 down to is_live_or_finished = ...
pattern = re.compile(r"        col_tgl1, col_tgl2, col_tgl3, col_tgl4.*?is_live_or_finished = is_finished_gw or is_ongoing_gw", re.DOTALL)

new_code = '''        is_finished_gw = selected_eval_gw in finished_gw_ids
        is_ongoing_gw = (selected_eval_gw == ongoing_gw)
        is_live_or_finished = is_finished_gw or is_ongoing_gw

        market_weight = 0.35
        factor_movement = True
        enable_betting = False
        super_team_mode = False

        if is_live_or_finished:
            col_tgl1, col_tgl2, col_tgl3, col_pad = st.columns([1.2, 1.3, 1.3, 6.2], vertical_alignment="center")
            with col_tgl1:
                pitch_view = st.toggle(":material/stadium: **Pitch View**", value=True, key="tab4_pitch_toggle")
            with col_tgl2:
                enable_comparison = st.toggle(":material/balance:  **Comparison**", value=False, key="tab4_compare_toggle")
            with col_tgl3:
                if enable_comparison:
                    super_team_mode = st.toggle(":material/star:  **Super Team**", value=False, key="tab4_super_team_toggle")
        else:
            col_tgl1, col_tgl2, col_tgl3, col_pad, col_tgl4, col_m1, col_m2 = st.columns(
                [1.3, 1.4, 1.4, 0.5, 1.8, 2.0, 1.6], 
                vertical_alignment="bottom"
            )
            with col_tgl1:
                pitch_view = st.toggle(":material/stadium: **Pitch View**", value=True, key="tab4_pitch_toggle")
            with col_tgl2:
                enable_comparison = st.toggle(":material/balance:  **Comparison**", value=False, key="tab4_compare_toggle")
            with col_tgl3:
                if enable_comparison:
                    super_team_mode = st.toggle(":material/star:  **Super Team**", value=False, key="tab4_super_team_toggle")
            
            with col_tgl4:
                enable_betting = st.toggle(":material/bar_chart:  **Betting Market**", value=True, key="tab4_enable_betting")
                
            if enable_betting:
                with col_m1:
                    market_weight = st.slider(
                        "Market Weight",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.35,
                        step=0.05,
                        format="%.2f",
                        key="tab4_mkt_weight",
                        help="0.0 = 100% Model | 1.0 = 100% Betting Odds",
                    )
                with col_m2:
                    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
                    factor_movement = st.checkbox(":material/bolt: Line Movement", value=True, key="tab4_factor_movement")'''

text = pattern.sub(new_code, text)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched toggles")
