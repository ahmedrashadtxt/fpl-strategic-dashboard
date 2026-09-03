import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

target = '''<span style="font-size:0.92rem; font-weight:700; color:{banner_title_col};">

          {f":material/style:Optimal Wildcard Squad ({horizon_gws}-GW Run)" if chip_mode == ":material/style:Wildcard" else (f":material/bolt:Optimal Free Hit Squad" if chip_mode == ":material/bolt:Free Hit" else f":material/sync:Transfer Squad ({horizon_gws}-GW Run)")}

          </span>'''
          
repl = '''<span style="font-size:0.92rem; font-weight:700; color:{banner_title_col};">{f":material/style:Optimal Wildcard Squad ({horizon_gws}-GW Run)" if chip_mode == ":material/style:Wildcard" else (f":material/bolt:Optimal Free Hit Squad" if chip_mode == ":material/bolt:Free Hit" else f":material/sync:Transfer Squad ({horizon_gws}-GW Run)")}</span>'''

text = text.replace(target, repl)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed span 2")
