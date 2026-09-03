import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('.head(20)', '.head(8)')
text = text.replace('.head(25)', '.head(12)')
text = text.replace('.head(30)', '.head(15)')

# Also replace timeLimit
text = text.replace('prob.solve(pulp.PULP_CBC_CMD(msg=False))', 'prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=3))')

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Speedup applied")
