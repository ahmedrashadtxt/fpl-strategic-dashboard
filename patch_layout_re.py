import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r"col_tgl1, col_tgl2, col_tgl3, col_tgl4, col_pad = st\.columns\(\[1\.3, 1\.4, 1\.4, 3\.0, 3\.5\], vertical_alignment=\"center\"\).*?st\.rerun\(\)", re.DOTALL)

new_logic = '''col_tgl1, col_tgl2, col_tgl3, col_tgl4, col_pad = st.columns([1.2, 1.3, 1.3, 1.5, 4.7], vertical_alignment="center")
        with col_tgl1:
            pitch_view = st.toggle(":material/stadium: **Pitch View**", value=True, key="tab4_pitch_toggle")
        with col_tgl2:
            enable_comparison = st.toggle(":material/balance:  **Comparison**", value=False, key="tab4_compare_toggle")
            
        super_team_mode = False
        with col_tgl3:
            if enable_comparison:
                super_team_mode = st.toggle(":material/star:  **Super Team**", value=False, key="tab4_super_team_toggle")
                
        with col_tgl4:
            enable_betting = st.toggle(":material/bar_chart:  **Betting Market xG**", value=True, key="tab4_enable_betting")
            
        market_weight = 0.35
        factor_movement = True
        
        if enable_betting:
            st.markdown("<div style='margin-top: -5px; margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            col_m1, col_m2, col_pad2 = st.columns([2.0, 1.5, 6.5], vertical_alignment="center")
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
                factor_movement = st.checkbox(":material/bolt:  Line Movement", value=True, key="tab4_factor_movement")

        # BELOW the row: Lock Lineup
        existing_snap = get_snapshot(conn, next_gw_id) if selected_eval_gw == next_gw_id else None
        snap_locked = existing_snap is not None
        
        if selected_eval_gw == next_gw_id:
            st.markdown("<div style='margin-top: 15px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
            col_lock_btn, col_lock_info = st.columns([1.5, 8.5], vertical_alignment="center")
            
            with col_lock_btn:
                if snap_locked:
                    lock_btn = st.button("Re-Lock Lineup", key="tab4_relock_btn")
                else:
                    lock_btn = st.button("Lock Lineup Snapshot", type="primary", key="tab4_lock_btn")
            
            with col_lock_info:
                if snap_locked:
                    st.markdown(
                        f"<div style='font-size: 0.85rem; color: #22c55e; font-weight: 600;'>Locked at {existing_snap['timestamp']}</div>",
                        unsafe_allow_html=True
                    )
                
            if lock_btn:
                save_snapshot(conn, next_gw_id, user_proj_xi_pts, optimal_formation, user_starters, user_bench)
                st.toast(f"Snapshot locked for GW{next_gw_id}!", icon=":material/lock:")
                st.rerun()'''

new_text = pattern.sub(new_logic, text)
if new_text != text:
    with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Patched layout via regex")
else:
    print("Regex failed to match")
