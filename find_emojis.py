import os
import re
import emoji

def extract_emojis(file_path):
  with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()
  return set(emoji.distinct_emoji_list(text))

for root, dirs, files in os.walk('.'):
  for file in files:
    if file.endswith('.py'):
      emojis = extract_emojis(os.path.join(root, file))
      if emojis:
        print(f"{file}:{' '.join(emojis)}")
