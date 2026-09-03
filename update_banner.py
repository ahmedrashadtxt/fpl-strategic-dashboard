import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the "Recommended Transfer Moves" title
pattern1 = r'(\s*)st\.markdown\("### :material/sync:  Recommended Transfer Moves"\)'
replacement1 = r'''\1if chip_mode == ":material/style:  Wildcard":
\1    st.markdown("### :material/style:  Optimal Wildcard Squad (Permanent Overhaul, 0 Hits)")
\1elif chip_mode == ":material/bolt:  Free Hit":
\1    st.markdown("### :material/bolt:  Optimal Free Hit Squad (1-Week Maximum Ceiling, 0 Hits)")
\1else:
\1    hit_val = max(0, len(swaps) - calc_ft) * 4
\1    st.markdown(f"### :material/my_location:  Optimal Transfer Route ({len(swaps)} moves, -{hit_val} pts)")'''

text = re.sub(pattern1, replacement1, text)

# Replace the right squad banner
pattern2 = r'(\s*)<span style="font-size: 0\.92rem; font-weight: 700; color: {banner_title_col};">:material/sync:  Transfer Squad \({horizon_gws}-GW Run\)</span>'
replacement2 = r'''\1<span style="font-size: 0.92rem; font-weight: 700; color: {banner_title_col};">
\1{f":material/style:  Optimal Wildcard Squad ({horizon_gws}-GW Run)" if chip_mode == ":material/style:  Wildcard" else (f":material/bolt:  Optimal Free Hit Squad" if chip_mode == ":material/bolt:  Free Hit" else f":material/sync:  Transfer Squad ({horizon_gws}-GW Run)")}
\1</span>'''

text = re.sub(pattern2, replacement2, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated result banner")
