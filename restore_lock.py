import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add imports if missing
if 'save_pre_gw_snapshot' not in text:
    import_statement = "\nfrom audit_db import save_pre_gw_snapshot, get_pre_gw_snapshot\n"
    # Find the last from data import
    match_data_import = re.search(r'from data import \((.*?)\)', text, re.DOTALL)
    if match_data_import:
        end_idx = match_data_import.end()
        text = text[:end_idx] + import_statement + text[end_idx:]

# 2. Inject the Lock button right before "if enable_comparison:"
insert_pattern = r'(\s*)if enable_comparison:'
match_insert = re.search(insert_pattern, text)
if match_insert:
    indent = match_insert.group(1)
    lock_code = f'''{indent}# Check if snapshot exists for lock UI
{indent}existing_snap = get_pre_gw_snapshot(conn, next_gw_id) if selected_eval_gw == next_gw_id else None
{indent}snap_locked = existing_snap is not None

{indent}if selected_eval_gw == next_gw_id:
{indent}    col_lock_btn, col_lock_info = st.columns([1.6, 4.4], vertical_alignment="center")
{indent}    with col_lock_btn:
{indent}        btn_label = "?? Re-Lock Lineup" if snap_locked else "?? Lock In Starting XI"
{indent}        if st.button(btn_label, key=f"commit_gw_{{selected_eval_gw}}", use_container_width=True):
{indent}            full_lineup_df = pd.concat([optimal_xi, optimal_bench], ignore_index=True)
{indent}            lineup_records = full_lineup_df.to_dict(orient="records")
{indent}            
{indent}            save_pre_gw_snapshot(
{indent}                conn=conn,
{indent}                gw=selected_eval_gw,
{indent}                lineup_data=lineup_records,
{indent}                chip=active_chip if active_chip != "None" else None,
{indent}                formation=optimal_formation,
{indent}                market_weight=market_weight if enable_betting else 0.0,
{indent}                factor_movement=factor_movement if enable_betting else False,
{indent}            )
{indent}            st.toast(f"GW{{selected_eval_gw}} optimal lineup committed to Audit Journal!", icon="?")
{indent}            st.rerun()

{indent}    with col_lock_info:
{indent}        if snap_locked:
{indent}            lock_time = existing_snap.get("created_at", "")[:16].replace("T", " ")
{indent}            st.markdown(f"<span style='color:#22c55e; font-size:0.8rem; margin-left:10px;'>? Locked at {{lock_time}}</span>", unsafe_allow_html=True)
'''
    text = text[:match_insert.start()] + lock_code + text[match_insert.start():]

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Restored Lock In Starting XI button")
