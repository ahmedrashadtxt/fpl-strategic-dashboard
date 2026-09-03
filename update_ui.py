import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'(\s*)st\.markdown\("#### :material/settings:  Parameters & Horizon"\).*?st\.metric\("Planned Moves"[^\n]*\)'

def replacer(match):
    indent = match.group(1)
    return f'''{indent}st.markdown("#### :material/settings:  Parameters & Horizon")
{indent}
{indent}chip_mode = st.radio("Strategy Mode:", ["Regular Transfers", ":material/style:  Wildcard", ":material/bolt:  Free Hit"], horizontal=True, index=0)
{indent}
{indent}if chip_mode == "Regular Transfers":
{indent}    c1, c2, c3, c4 = st.columns([1.6, 1.0, 1.0, 1.4], vertical_alignment="bottom")
{indent}    with c1:
{indent}        horizon_gws = st.selectbox(
{indent}            "Evaluation Horizon",
{indent}            options=[1, 2, 3, 5],
{indent}            format_func=lambda x: f"Next {{x}} Gameweek{{'s' if x > 1 else ''}} (GW{{next_gw}}GW{{next_gw + x - 1}})",
{indent}            index=2,
{indent}        )
{indent}    with c2:
{indent}        ft_selected = st.number_input("Free Transfers", min_value=1, max_value=5, value=calc_ft, step=1)
{indent}    with c3:
{indent}        max_hits = st.number_input("Max Hits (-4)", min_value=0, max_value=5, value=0, step=1)
{indent}    with c4:
{indent}        total_allowed_transfers = int(ft_selected + max_hits)
{indent}        hit_cost_str = f"(-{{max_hits * 4}} pts)" if max_hits > 0 else "(0 pts)"
{indent}        st.metric("Planned Moves", f"{{total_allowed_transfers}} Transfers", delta=hit_cost_str if max_hits > 0 else None, delta_color="inverse")
{indent}elif chip_mode == ":material/style:  Wildcard":
{indent}    horizon_gws = st.selectbox(
{indent}        "Evaluation Horizon",
{indent}        options=[3, 5, 8],
{indent}        format_func=lambda x: f"Next {{x}} Gameweeks (GW{{next_gw}}GW{{next_gw + x - 1}})",
{indent}        index=1,
{indent}    )
{indent}    ft_selected = 15
{indent}    max_hits = 0
{indent}    total_allowed_transfers = 15
{indent}    team_val = entry_hist.get("value", mgr_data.get("last_deadline_value", 1000)) / 10.0
{indent}    st.info(":material/style:  **Wildcard Active**: Optimizing a permanent 15-man squad over the selected horizon with 0 point deductions.")
{indent}    st.metric("Available Budget", f"£{{team_val:.1f}}m")
{indent}else:
{indent}    horizon_gws = 1
{indent}    st.markdown("**Evaluation Horizon:** Next 1 Gameweek (Locked for Free Hit)")
{indent}    ft_selected = 15
{indent}    max_hits = 0
{indent}    total_allowed_transfers = 15
{indent}    team_val = entry_hist.get("value", mgr_data.get("last_deadline_value", 1000)) / 10.0
{indent}    st.info(":material/bolt:  **Free Hit Active**: Optimizing a single-gameweek £100m+ roster with 0 point deductions. Reverts automatically next gameweek.")
{indent}    st.metric("Available Budget", f"£{{team_val:.1f}}m")
'''

text = re.sub(pattern, replacer, text, flags=re.DOTALL)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("UI updated")
