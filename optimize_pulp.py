import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

# Replace slow .loc lookups with dictionary lookups in pulp solver
pattern = r'# Budget constraint[\s\S]*?prob \+= objective'

replacement = r'''# Pre-build dictionaries for fast lookup
  cost_dict = avail.set_index("id")["Cost"].to_dict()
  xp_dict = avail.set_index("id")["Horizon_xP"].to_dict()
  
  # Budget constraint
  prob += pulp.lpSum(player_vars[pid] * cost_dict[pid] for pid in player_vars) <= team_value
  
  # Objective:Maximize starting XI points + 0.1 * bench points
  objective = pulp.lpSum(
    starter_vars[pid] * xp_dict[pid] +
    0.1 * (player_vars[pid] - starter_vars[pid]) * xp_dict[pid]
    for pid in player_vars
  )
  prob += objective'''

text = re.sub(pattern, replacement, text)

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
print("Optimized PuLP builder")
