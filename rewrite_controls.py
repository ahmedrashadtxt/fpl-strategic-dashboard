import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to find the entire block from col_tgl1 all the way to is_finished_gw = selected_eval_gw in finished_gw_ids
pattern = r'(col_tgl1, col_tgl2, col_tgl3, col_tgl4 = st\.columns\(\[1\.2, 1\.3, 3\.0, 2\.5\]\).*?)(is_finished_gw = selected_eval_gw in finished_gw_ids)'

def replace_block(match):
    old_block = match.group(1)
    
    # We will build a new block
    # Layout:
    # Top row: Pitch View, Comparison, Super Team, Betting Market xG
    # col_tgl1 (Pitch View), col_tgl2 (Comparison), col_tgl3 (Super Team), col_tgl4 (Betting)
    # Then a separate row below for Lock Button
    
    new_block = '''
        col_tgl1, col_tgl2, col_tgl3, col_tgl4 = st.columns([1.5, 1.6, 1.6, 3.5], vertical_alignment="center")
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
                col_m1, col_m2 = st.columns([1.6, 1.0])
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
            st.markdown("<div style='margin-top: 10px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
            col_lock_btn, col_lock_info = st.columns([2.0, 8.0], vertical_alignment="center")
            
            with col_lock_btn:
                btn_label = ":material/lock:  Re-Lock Lineup" if snap_locked else ":material/lock:  Lock In Starting XI"
                if st.button(btn_label, key=f"commit_gw_{selected_eval_gw}", use_container_width=True):
                    full_lineup_df = pd.concat([optimal_xi, optimal_bench], ignore_index=True)
                    lineup_records = full_lineup_df.to_dict(orient="records")
                    
                    save_pre_gw_snapshot(
                        conn=conn,
                        gw=selected_eval_gw,
                        lineup_data=lineup_records,
                        chip=active_chip if active_chip != "None" else None,
                        formation=optimal_formation,
                        market_weight=market_weight if enable_betting else 0.0,
                        factor_movement=factor_movement if enable_betting else False,
                    )
                    st.toast(f"GW{selected_eval_gw} optimal lineup committed to Audit Journal!", icon=":material/check_circle: ")
                    st.rerun()
                    
            with col_lock_info:
                if snap_locked:
                    lock_time = existing_snap.get("created_at", "")[:16].replace("T", " ")
                    st.markdown(f"<span style='color:#22c55e; font-size:0.85rem; font-weight:600;'>:material/check_circle:  Locked at {lock_time}</span>", unsafe_allow_html=True)
        
        '''
    return new_block + match.group(2)

text = re.sub(pattern, replace_block, text, flags=re.DOTALL)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Rewrote controls block")
