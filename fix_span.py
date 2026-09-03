import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

pattern = r'(<span style="font-size:0\.92rem; font-weight:700; color:\{banner_title_col\};">)\n+\s*(\{f".*?\}\})\n+\s*(</span>)'
replacement = r'\1\2\3'
text = re.sub(pattern, replacement, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Fixed span")
