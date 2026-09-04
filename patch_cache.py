import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('fetch_manager_entry.clear()', 'fetch_manager_entry.clear()\n                fetch_manager_transfers.clear()')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched cache clear")
