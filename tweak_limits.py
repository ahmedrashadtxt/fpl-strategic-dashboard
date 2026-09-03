import re

with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('{"GKP": 15, "DEF": 40, "MID": 45, "FWD": 25}', '{"GKP": 8, "DEF": 20, "MID": 25, "FWD": 15}')

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Tweaked limits")
