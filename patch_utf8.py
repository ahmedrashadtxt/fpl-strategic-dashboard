with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('', '£')
text = text.replace('f"£{fmt_num', 'f"£{fmt_num') 

# Fix opponent
text = text.replace('Opponent", "£"', 'Opponent", "—"')
text = text.replace('Opponent", "—"', 'Opponent", "—"')
text = text.replace('Team", "")))', 'Team", "")))')
text = text.replace('f\'<span class="tt-badge">{team} £ {pos} £ {cost_str}</span>\'', 'f\'<span class="tt-badge">{team} · {pos} · {cost_str}</span>\'')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed encoding")
