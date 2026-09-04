import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('live_mins = p.get("Live_Mins", 0)', 'live_mins = p.get("Live_Mins") or 0')
text = text.replace('live_bonus = p.get("Live_Bonus", 0)', 'live_bonus = p.get("Live_Bonus") or 0')
text = text.replace('live_bps = p.get("Live_BPS", 0)', 'live_bps = p.get("Live_BPS") or 0')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched pitch component for None safety")
