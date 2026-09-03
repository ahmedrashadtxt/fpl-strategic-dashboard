import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

injection = '''  state_key = f"transfer_solve_{mgr_to_use}_{chip_mode}_{horizon_gws}_{ft_selected}_{max_hits}_{market_weight}"\n  results_slot = st.empty()'''

text = text.replace('  results_slot = st.empty()', injection)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
