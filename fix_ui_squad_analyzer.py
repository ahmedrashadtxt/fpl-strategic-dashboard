import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

pattern = r'col_tgl1, col_tgl2, col_tgl3, col_tgl4 = st\.columns\(\[1\.5, 1\.8, 1\.7, 2\.8\]\).*?super_team_mode = st\.toggle\(":material/star:\*\*Super Team\*\*", value=False, key="tab4_super_team_toggle"\)\n\s*with col_tgl4:'

# Let's extract the exact block manually.
