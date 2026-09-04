with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"Target Signing :material/my_location: "', '"Target Signing"')

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched display_ledger Role")
