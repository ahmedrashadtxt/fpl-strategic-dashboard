with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix raw HTML icons
text = text.replace(':material/lightbulb:How to find your Team ID:', 'How to find your Team ID:')
text = text.replace(':material/arrow_right_alt:The number right after', '&#8594; The number right after')

# Fix badge_label missing spaces
old_badge = 'badge_label = f":material/person:{display_title}  #{curr_id} :material/edit:" if curr_id else " Enter FPL ID"'
# We will use regex to catch any encoding of the dot
import re
pattern = re.compile(r'badge_label = f":material/person:\{display_title\}(.*?):material/edit:" if curr_id else " Enter FPL ID"')

def repl(match):
    return f'badge_label = f":material/person: {{display_title}}{match.group(1)} :material/edit:" if curr_id else ":material/person: Enter FPL ID"'

text = pattern.sub(repl, text)

# Just in case the regex doesn't match due to the dot:
text = text.replace('f":material/person:{display_title}', 'f":material/person: {display_title}')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Patched app.py")
