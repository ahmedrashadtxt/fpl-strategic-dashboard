import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

# Remove everything from st.markdown("#### :material/settings:Parameters & Horizon") to chip_mode
pattern = r'(st\.markdown\("#### :material/settings:Parameters & Horizon"\)).*?(chip_mode = st\.radio\("Strategy Mode:", \["Regular Transfers", ":material/style:Wildcard", ":material/bolt:Free Hit"\], horizontal=True, index=0\))'
replacement = r'''\1

  if pick_ids:
    placeholders = ",".join(["?"] * len(pick_ids))
    cur = conn.cursor()
    cur.execute(f"SELECT SUM(now_cost) FROM players WHERE id IN ({placeholders})", pick_ids)
    squad_sell = round((cur.fetchone()[0] or 1000) / 10.0, 1)
  else:
    squad_sell = 100.0
  itb_val = entry_hist.get("bank", mgr_data.get("last_deadline_bank", 0)) / 10.0
  team_val = round(squad_sell + itb_val, 1)

  \2'''
text = re.sub(pattern, replacement, text, flags=re.DOTALL)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Cleaned up duplicates")
