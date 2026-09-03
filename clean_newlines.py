import re

with open('tabs/squad_analyzer.py', 'r', encoding='utf-8') as f:
  text = f.read()

# Replace \n\n\n with \n repeatedly
while '\n\n\n' in text:
  text = text.replace('\n\n\n', '\n\n')

with open('tabs/squad_analyzer.py', 'w', encoding='utf-8') as f:
  f.write(text)
