import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

pattern = r'(\s*)is_long_range = \(target_chip_gw is not None\) and \(target_chip_gw - next_gw_id >= 4\)[\s\S]*?if is_long_range else ""\n\s*\)'
text = re.sub(pattern, '', text)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
