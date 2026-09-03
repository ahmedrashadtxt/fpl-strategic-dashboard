import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

text = text.replace('\ncol_gw_sel, col_gw_ref =', '\n    col_gw_sel, col_gw_ref =')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed indent")
