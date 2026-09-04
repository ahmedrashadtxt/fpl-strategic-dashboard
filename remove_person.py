with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Look for badge_label assignment
pattern = re.compile(r'badge_label = f":material/person: \{display_title\}(.*?) :material/edit:" if curr_id else ":material/person: Enter FPL ID"')

def repl(match):
    return f'badge_label = f"{{display_title}}{match.group(1)} (Edit)" if curr_id else "Enter FPL ID"'

text = pattern.sub(repl, text)

# Just in case regex fails because of encoding character
text = text.replace('badge_label = f":material/person: {display_title}  #{curr_id}  :material/edit:" if curr_id else ":material/person: Enter FPL ID"',
                   'badge_label = f"{display_title}  #{curr_id} (Edit)" if curr_id else "Enter FPL ID"')

# If there's any other variant:
import sys
if ':material/person:' in text:
    print('Still found material/person!')
    text = text.replace(':material/person: ', '')
    text = text.replace(' :material/edit:', ' (Edit)')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Removed material person")
