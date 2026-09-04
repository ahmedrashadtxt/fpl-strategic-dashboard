with open('tabs/transfer_analyzer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('tags.append(("Target In :material/my_location: ", "yellow"))', 'tags.append(("Target In", "yellow"))')

with open('tabs/transfer_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched target tags")
