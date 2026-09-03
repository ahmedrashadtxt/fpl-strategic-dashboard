import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

text = re.sub(r'\s*team_val = entry_hist\.get\("value", mgr_data\.get\("last_deadline_value", 1000\)\) / 10\.0', '', text)
text = re.sub(r'\s*itb_val = entry_hist\.get\("bank", mgr_data\.get\("last_deadline_bank", 0\)\) / 10\.0', '', text)
text = re.sub(r'\s*squad_sell = round\(team_val - itb_val, 1\)', '', text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Cleaned old budget vars")
