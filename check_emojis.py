import os
for file in ['app.py'] + [os.path.join('tabs', f) for f in os.listdir('tabs') if f.endswith('.py')]:
  with open(file, 'r', encoding='utf-8') as f:
    text = f.read()
  chars = set(c for c in text if ord(c) > 8192)
  # ignore common safe unicode chars
  safe = set('?????????')
  chars = chars - safe
  if chars:
    print(f"{file}:{' '.join(chars)}")
