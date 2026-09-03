import os

for root, dirs, files in os.walk('.'):
  if '.git' in root or '.venv' in root:continue
  for file in files:
    if file.endswith('.py'):
      with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
        text = f.read()
      # print characters > 127
      chars = set(c for c in text if ord(c) > 127)
      # filter out £, ·, °, etc.
      chars = set(c for c in text if ord(c) > 8192)
      if chars:
        print(f"{file}:{' '.join(chars)}")
