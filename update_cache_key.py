import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add the cache key definition right before the Solve button
cache_key_code = '''    state_key = f"transfer_solve_{mgr_to_use}_{chip_mode}_{horizon_gws}_{ft_selected}_{max_hits}_{market_weight}"'''
# Find the button
pattern_btn = r'(\s*)if st\.button\(":material/sync:  Solve Transfers", type="primary", use_container_width=True\):'
match_btn = re.search(pattern_btn, text)
if match_btn:
    indent = match_btn.group(1)
    text = text[:match_btn.start()] + f"{indent}{cache_key_code.strip()}" + text[match_btn.start():]

# 2. Replace "transfer_result" with state_key
text = text.replace('st.session_state["transfer_result"]', 'st.session_state[state_key]')
text = text.replace('"transfer_result" not in st.session_state', 'state_key not in st.session_state')

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated cache key")
