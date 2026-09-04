import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the old block
pattern1 = re.compile(r"        # BELOW the row: Lock Lineup\n.*?(?=        is_finished_gw = selected_eval_gw in finished_gw_ids)", re.DOTALL)
text = pattern1.sub("", text)

# 2. Insert the new block
target2 = '''            squad_rating = round((0.50 * fdr_ease_pct) + (0.50 * pts_index_pct), 1)

            if enable_comparison:'''

new_block = '''            squad_rating = round((0.50 * fdr_ease_pct) + (0.50 * pts_index_pct), 1)

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
                        lock_time = existing_snap.get("created_at", "")[:16].replace("T", " ")
                        st.markdown(
                            f"<div style='font-size: 0.85rem; color: #22c55e; font-weight: 600;'>Locked at {lock_time}</div>",
                            unsafe_allow_html=True
                        )
                    
                if lock_btn:
                    starters_list = optimal_xi.to_dict('records')
                    for p in starters_list:
                        p['is_starter'] = True
                    bench_list = optimal_bench.to_dict('records')
                    for p in bench_list:
                        p['is_starter'] = False
                    lineup_data = starters_list + bench_list
                    
                    save_pre_gw_snapshot(
                        conn=conn, 
                        gw=next_gw_id, 
                        lineup_data=lineup_data, 
                        formation=optimal_formation,
                        market_weight=market_weight,
                        factor_movement=factor_movement,
                        chip=active_chip if chip_active_on_gw else None
                    )
                    st.toast(f"Snapshot locked for GW{next_gw_id}!", icon=":material/lock:")
                    st.rerun()

            if enable_comparison:'''

text = text.replace(target2, new_block)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched squad_analyzer.py")
