import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

# Replace import
text = text.replace('from audit_db import save_pre_gw_snapshot, get_pre_gw_snapshot', 'from audit_db import save_pre_gw_snapshot, get_snapshot')

# Replace function call
text = text.replace('get_pre_gw_snapshot(conn, next_gw_id)', 'get_snapshot(conn, next_gw_id)')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed import")
