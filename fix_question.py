import os

for root, dirs, files in os.walk('.'):
    if '.git' in root or '.venv' in root: continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if '?' in text:
                text = text.replace('?', '?')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
