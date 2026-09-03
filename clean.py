import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

pattern = r'#facc15 !important;\s+font-weight:700 !important;\s+\}\}\s+</style>\s+""",\s+unsafe_allow_html=True,\s+\)\s+'
text = re.sub(pattern, '', text)

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Cleaned up orphaned CSS string")
