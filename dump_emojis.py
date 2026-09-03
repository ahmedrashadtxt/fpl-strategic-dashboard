import os
with open('emojis.txt', 'w', encoding='utf-8') as out:
  for root, dirs, files in os.walk('.'):
    if '.git' in root or '.venv' in root:continue
    for file in files:
      if file.endswith('.py'):
        try:
          with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
            text = f.read()
          chars = set(c for c in text if ord(c) > 8192)
          if chars:
            out.write(f"{file}:{' '.join(chars)}\n")
        except Exception:
          pass
