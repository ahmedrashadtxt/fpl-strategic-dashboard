import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

# I will find the chip_mode definition
chip_mode_pattern = r'(chip_mode = st\.radio\("Strategy Mode:", \["Regular Transfers", ":material/style:Wildcard", ":material/bolt:Free Hit"\], horizontal=True, index=0\))'

budget_logic = '''
  if pick_ids:
    placeholders = ",".join(["?"] * len(pick_ids))
    cur = conn.cursor()
    cur.execute(f"SELECT SUM(now_cost) FROM players WHERE id IN ({placeholders})", pick_ids)
    squad_sell = round((cur.fetchone()[0] or 1000) / 10.0, 1)
  else:
    squad_sell = 100.0
  itb_val = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
  team_val = round(squad_sell + itb_val, 1)
'''

# Insert the logic right before chip_mode
text = re.sub(chip_mode_pattern, budget_logic + r'\n  \1', text)

# Now remove the old team_val calculations in the if blocks
old_budget_pattern = r'(\s*)team_val = entry_hist\.get\("value", mgr_data\.get\("last_deadline_value", 1000\)\) / 10\.0\n\s*itb_val = entry_hist\.get\("bank", mgr_data\.get\("last_deadline_bank", 0\)\) / 10\.0\n\s*squad_sell = round\(team_val - itb_val, 1\)'
text = re.sub(old_budget_pattern, '', text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Applied budget fix")
